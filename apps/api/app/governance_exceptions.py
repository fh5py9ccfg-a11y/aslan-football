from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class PolicyException:
    exception_id: str
    tenant_id: str
    policy_id: str
    resource: str
    reason: str
    risk_level: str
    approved_by: str
    starts_at: int
    expires_at: int
    status: str
    created_at: int


@dataclass(frozen=True)
class RiskAcceptance:
    acceptance_id: str
    tenant_id: str
    exception_id: str
    risk_owner: str
    residual_risk: str
    compensating_controls: tuple[str, ...]
    decision: str
    decided_at: int


@dataclass(frozen=True)
class FrameworkMapping:
    mapping_id: str
    tenant_id: str
    framework: str
    framework_control: str
    governance_control_id: str
    evidence_types: tuple[str, ...]
    created_at: int


class GovernanceExceptionError(RuntimeError):
    pass


class GovernanceExceptionValidationError(ValueError):
    pass


class RedisGovernanceExceptionRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:governance-exceptions",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_exception(self, item: PolicyException) -> PolicyException:
        self.client.setex(
            self._exception_key(item.exception_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False, separators=(",", ":")),
        )
        self.client.sadd(
            self._tenant_exception_index(item.tenant_id),
            item.exception_id,
        )
        return item

    def get_exception(self, exception_id: str) -> PolicyException | None:
        payload = self.client.get(self._exception_key(exception_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return PolicyException(**json.loads(payload))

    def list_exceptions(self, tenant_id: str) -> tuple[PolicyException, ...]:
        items = []
        for exception_id in self.client.smembers(
            self._tenant_exception_index(tenant_id)
        ):
            if isinstance(exception_id, bytes):
                exception_id = exception_id.decode("utf-8")
            item = self.get_exception(str(exception_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.expires_at)
        return tuple(items)

    def save_acceptance(self, item: RiskAcceptance) -> RiskAcceptance:
        payload = {
            **item.__dict__,
            "compensating_controls": list(item.compensating_controls),
        }
        self.client.setex(
            self._acceptance_key(item.acceptance_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        )
        self.client.sadd(
            self._exception_acceptance_index(item.exception_id),
            item.acceptance_id,
        )
        return item

    def list_acceptances(self, exception_id: str) -> tuple[RiskAcceptance, ...]:
        items = []
        for acceptance_id in self.client.smembers(
            self._exception_acceptance_index(exception_id)
        ):
            if isinstance(acceptance_id, bytes):
                acceptance_id = acceptance_id.decode("utf-8")
            payload = self.client.get(
                self._acceptance_key(str(acceptance_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            data["compensating_controls"] = tuple(
                data["compensating_controls"]
            )
            items.append(RiskAcceptance(**data))
        items.sort(key=lambda item: item.decided_at)
        return tuple(items)

    def save_mapping(self, item: FrameworkMapping) -> FrameworkMapping:
        payload = {
            **item.__dict__,
            "evidence_types": list(item.evidence_types),
        }
        self.client.setex(
            self._mapping_key(item.mapping_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
        )
        self.client.sadd(
            self._tenant_mapping_index(item.tenant_id),
            item.mapping_id,
        )
        return item

    def list_mappings(self, tenant_id: str) -> tuple[FrameworkMapping, ...]:
        items = []
        for mapping_id in self.client.smembers(
            self._tenant_mapping_index(tenant_id)
        ):
            if isinstance(mapping_id, bytes):
                mapping_id = mapping_id.decode("utf-8")
            payload = self.client.get(self._mapping_key(str(mapping_id)))
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            data["evidence_types"] = tuple(data["evidence_types"])
            items.append(FrameworkMapping(**data))
        items.sort(
            key=lambda item: (
                item.framework,
                item.framework_control,
            )
        )
        return tuple(items)

    def _exception_key(self, exception_id: str) -> str:
        return f"{self.prefix}:exception:{exception_id}"

    def _tenant_exception_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:exceptions:{tenant_id}"

    def _acceptance_key(self, acceptance_id: str) -> str:
        return f"{self.prefix}:acceptance:{acceptance_id}"

    def _exception_acceptance_index(self, exception_id: str) -> str:
        return f"{self.prefix}:acceptances:{exception_id}"

    def _mapping_key(self, mapping_id: str) -> str:
        return f"{self.prefix}:mapping:{mapping_id}"

    def _tenant_mapping_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:mappings:{tenant_id}"


class GovernanceExceptionService:
    VALID_RISKS = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}
    VALID_FRAMEWORKS = {"ISO27001", "SOC2", "KVKK", "GDPR"}

    def __init__(self, *, repository, governance_service):
        self.repository = repository
        self.governance_service = governance_service

    def create_exception(
        self,
        *,
        exception_id: str,
        tenant_id: str,
        policy_id: str,
        resource: str,
        reason: str,
        risk_level: str,
        approved_by: str,
        starts_at: int,
        expires_at: int,
        now: int | None = None,
    ) -> PolicyException:
        policy = self.governance_service.repository.get_policy(
            tenant_id=tenant_id,
            policy_id=policy_id,
        )
        if policy is None:
            raise KeyError("Policy bulunamadı")
        risk = risk_level.upper()
        if risk not in self.VALID_RISKS:
            raise GovernanceExceptionValidationError("Geçersiz risk seviyesi")
        if expires_at <= starts_at:
            raise GovernanceExceptionValidationError(
                "Exception bitişi başlangıçtan büyük olmalıdır"
            )
        if len(reason.strip()) < 8:
            raise GovernanceExceptionValidationError(
                "Exception nedeni açıklayıcı olmalıdır"
            )

        current = int(now if now is not None else time.time())
        item = PolicyException(
            exception_id=exception_id,
            tenant_id=tenant_id,
            policy_id=policy_id,
            resource=resource,
            reason=reason,
            risk_level=risk,
            approved_by=approved_by,
            starts_at=starts_at,
            expires_at=expires_at,
            status="ACTIVE",
            created_at=current,
        )
        return self.repository.save_exception(item)

    def accept_risk(
        self,
        *,
        acceptance_id: str,
        tenant_id: str,
        exception_id: str,
        risk_owner: str,
        residual_risk: str,
        compensating_controls: tuple[str, ...],
        decision: str,
        now: int | None = None,
    ) -> RiskAcceptance:
        exception = self.repository.get_exception(exception_id)
        if exception is None or exception.tenant_id != tenant_id:
            raise KeyError("Policy exception bulunamadı")
        normalized = decision.upper()
        if normalized not in {"ACCEPTED", "REJECTED"}:
            raise GovernanceExceptionValidationError(
                "Risk kararı ACCEPTED veya REJECTED olmalıdır"
            )
        if normalized == "ACCEPTED" and not compensating_controls:
            raise GovernanceExceptionValidationError(
                "Kabul edilen risk için compensating control gereklidir"
            )

        item = RiskAcceptance(
            acceptance_id=acceptance_id,
            tenant_id=tenant_id,
            exception_id=exception_id,
            risk_owner=risk_owner,
            residual_risk=residual_risk,
            compensating_controls=compensating_controls,
            decision=normalized,
            decided_at=int(now if now is not None else time.time()),
        )
        self.repository.save_acceptance(item)

        status = "APPROVED" if normalized == "ACCEPTED" else "REJECTED"
        self.repository.save_exception(
            PolicyException(
                **{
                    **exception.__dict__,
                    "status": status,
                }
            )
        )
        return item

    def create_mapping(
        self,
        *,
        mapping_id: str,
        tenant_id: str,
        framework: str,
        framework_control: str,
        governance_control_id: str,
        evidence_types: tuple[str, ...],
        now: int | None = None,
    ) -> FrameworkMapping:
        normalized = framework.upper()
        if normalized not in self.VALID_FRAMEWORKS:
            raise GovernanceExceptionValidationError(
                "Desteklenmeyen compliance framework"
            )
        controls = self.governance_service.repository.list_controls(tenant_id)
        if not any(
            item.control_id == governance_control_id
            for item in controls
        ):
            raise KeyError("Governance control bulunamadı")

        item = FrameworkMapping(
            mapping_id=mapping_id,
            tenant_id=tenant_id,
            framework=normalized,
            framework_control=framework_control,
            governance_control_id=governance_control_id,
            evidence_types=tuple(
                item.upper() for item in evidence_types
            ),
            created_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_mapping(item)

    def exception_status(
        self,
        *,
        exception_id: str,
        now: int | None = None,
    ) -> PolicyException:
        item = self.repository.get_exception(exception_id)
        if item is None:
            raise KeyError("Policy exception bulunamadı")
        current = int(now if now is not None else time.time())
        if current > item.expires_at and item.status not in {
            "EXPIRED",
            "REJECTED",
        }:
            item = PolicyException(
                **{
                    **item.__dict__,
                    "status": "EXPIRED",
                }
            )
            self.repository.save_exception(item)
        return item

    def framework_report(
        self,
        *,
        tenant_id: str,
        framework: str,
        now: int | None = None,
    ) -> dict:
        normalized = framework.upper()
        mappings = tuple(
            item
            for item in self.repository.list_mappings(tenant_id)
            if item.framework == normalized
        )
        evidence_types = {
            item.evidence_type
            for item in self.governance_service.repository.list_evidence(
                tenant_id
            )
        }
        covered = 0
        gaps = []
        for mapping in mappings:
            missing = [
                item
                for item in mapping.evidence_types
                if item not in evidence_types
            ]
            if missing:
                gaps.append(
                    f"{mapping.framework_control}: "
                    f"evidence eksik={','.join(missing)}"
                )
            else:
                covered += 1

        active_exceptions = []
        for exception in self.repository.list_exceptions(tenant_id):
            current = self.exception_status(
                exception_id=exception.exception_id,
                now=now,
            )
            if current.status in {"ACTIVE", "APPROVED"}:
                active_exceptions.append(current.exception_id)

        total = len(mappings)
        return {
            "tenant_id": tenant_id,
            "framework": normalized,
            "total_controls": total,
            "covered_controls": covered,
            "coverage_percent": (
                100.0
                if total == 0
                else round(covered / total * 100.0, 2)
            ),
            "active_exceptions": active_exceptions,
            "gaps": gaps,
            "generated_at": int(
                now if now is not None else time.time()
            ),
        }
