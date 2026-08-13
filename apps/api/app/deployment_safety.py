from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class FreezeWindow:
    freeze_id: str
    tenant_id: str
    starts_at: int
    ends_at: int
    reason: str
    emergency_bypass_allowed: bool
    enabled: bool
    created_by: str
    created_at: int


@dataclass(frozen=True)
class DeploymentApproval:
    approval_id: str
    tenant_id: str
    release_id: str
    role: str
    actor: str
    decision: str
    comment: str
    decided_at: int


@dataclass(frozen=True)
class DeploymentRiskSnapshot:
    release_id: str
    tenant_id: str
    reliability_score: int
    warning_slos: int
    critical_slos: int
    rollout_status: str
    verification_status: str
    changed_files: int
    affected_services: int
    risk_score: int
    risk_level: str
    reasons: tuple[str, ...]
    calculated_at: int


@dataclass(frozen=True)
class DeploymentSafetyDecision:
    decision_id: str
    tenant_id: str
    release_id: str
    allowed: bool
    status: str
    reason: str
    emergency: bool
    override_actor: str | None
    override_reason: str | None
    risk_score: int
    freeze_id: str | None
    approvals_required: tuple[str, ...]
    approvals_received: tuple[str, ...]
    decided_at: int


class DeploymentSafetyError(RuntimeError):
    pass


class DeploymentSafetyValidationError(ValueError):
    pass


class RedisDeploymentSafetyRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:deployment-safety",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_freeze(
        self,
        freeze: FreezeWindow,
    ) -> FreezeWindow:
        self.client.setex(
            self._freeze_key(freeze.freeze_id),
            self.ttl_seconds,
            json.dumps(
                freeze.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._freeze_index(freeze.tenant_id),
            freeze.freeze_id,
        )
        return freeze

    def list_freezes(
        self,
        tenant_id: str,
    ) -> tuple[FreezeWindow, ...]:
        items = []
        for freeze_id in self.client.smembers(
            self._freeze_index(tenant_id)
        ):
            if isinstance(freeze_id, bytes):
                freeze_id = freeze_id.decode("utf-8")
            payload = self.client.get(
                self._freeze_key(str(freeze_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                FreezeWindow(**json.loads(payload))
            )
        items.sort(key=lambda item: item.starts_at)
        return tuple(items)

    def active_freeze(
        self,
        *,
        tenant_id: str,
        now: int,
    ) -> FreezeWindow | None:
        for item in self.list_freezes(tenant_id):
            if (
                item.enabled
                and item.starts_at <= now <= item.ends_at
            ):
                return item
        return None

    def save_approval(
        self,
        approval: DeploymentApproval,
    ) -> DeploymentApproval:
        self.client.setex(
            self._approval_key(approval.approval_id),
            self.ttl_seconds,
            json.dumps(
                approval.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._approval_index(
                approval.tenant_id,
                approval.release_id,
            ),
            approval.approval_id,
        )
        return approval

    def list_approvals(
        self,
        *,
        tenant_id: str,
        release_id: str,
    ) -> tuple[DeploymentApproval, ...]:
        items = []
        for approval_id in self.client.smembers(
            self._approval_index(
                tenant_id,
                release_id,
            )
        ):
            if isinstance(approval_id, bytes):
                approval_id = approval_id.decode("utf-8")
            payload = self.client.get(
                self._approval_key(str(approval_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                DeploymentApproval(**json.loads(payload))
            )
        items.sort(key=lambda item: item.decided_at)
        return tuple(items)

    def save_risk(
        self,
        snapshot: DeploymentRiskSnapshot,
    ) -> DeploymentRiskSnapshot:
        payload = {
            **snapshot.__dict__,
            "reasons": list(snapshot.reasons),
        }
        self.client.setex(
            self._risk_key(
                snapshot.tenant_id,
                snapshot.release_id,
            ),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        return snapshot

    def get_risk(
        self,
        *,
        tenant_id: str,
        release_id: str,
    ) -> DeploymentRiskSnapshot | None:
        payload = self.client.get(
            self._risk_key(tenant_id, release_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["reasons"] = tuple(data["reasons"])
        return DeploymentRiskSnapshot(**data)

    def save_decision(
        self,
        decision: DeploymentSafetyDecision,
    ) -> DeploymentSafetyDecision:
        payload = {
            **decision.__dict__,
            "approvals_required": list(
                decision.approvals_required
            ),
            "approvals_received": list(
                decision.approvals_received
            ),
        }
        self.client.setex(
            self._decision_key(decision.decision_id),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._decision_index(decision.tenant_id),
            decision.decision_id,
        )
        return decision

    def list_decisions(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
    ) -> tuple[DeploymentSafetyDecision, ...]:
        items = []
        for decision_id in self.client.smembers(
            self._decision_index(tenant_id)
        ):
            if isinstance(decision_id, bytes):
                decision_id = decision_id.decode("utf-8")
            payload = self.client.get(
                self._decision_key(str(decision_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            data["approvals_required"] = tuple(
                data["approvals_required"]
            )
            data["approvals_received"] = tuple(
                data["approvals_received"]
            )
            items.append(
                DeploymentSafetyDecision(**data)
            )
        items.sort(
            key=lambda item: item.decided_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def _freeze_key(self, freeze_id: str) -> str:
        return f"{self.prefix}:freeze:{freeze_id}"

    def _freeze_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:freezes:{tenant_id}"

    def _approval_key(self, approval_id: str) -> str:
        return f"{self.prefix}:approval:{approval_id}"

    def _approval_index(
        self,
        tenant_id: str,
        release_id: str,
    ) -> str:
        return (
            f"{self.prefix}:approvals:"
            f"{tenant_id}:{release_id}"
        )

    def _risk_key(
        self,
        tenant_id: str,
        release_id: str,
    ) -> str:
        return (
            f"{self.prefix}:risk:"
            f"{tenant_id}:{release_id}"
        )

    def _decision_key(self, decision_id: str) -> str:
        return f"{self.prefix}:decision:{decision_id}"

    def _decision_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:decisions:{tenant_id}"


class DeploymentSafetyService:
    DEFAULT_APPROVAL_ROLES = (
        "ops",
        "mlops",
    )

    def __init__(
        self,
        *,
        repository,
        reliability_service,
        progressive_delivery_service,
        deployment_verification_service,
    ):
        self.repository = repository
        self.reliability_service = reliability_service
        self.progressive_delivery_service = (
            progressive_delivery_service
        )
        self.deployment_verification_service = (
            deployment_verification_service
        )

    def create_freeze(
        self,
        *,
        freeze_id: str,
        tenant_id: str,
        starts_at: int,
        ends_at: int,
        reason: str,
        emergency_bypass_allowed: bool,
        created_by: str,
        now: int | None = None,
    ) -> FreezeWindow:
        if ends_at <= starts_at:
            raise DeploymentSafetyValidationError(
                "Freeze bitiş zamanı başlangıçtan büyük olmalıdır"
            )
        if len(reason.strip()) < 5:
            raise DeploymentSafetyValidationError(
                "Freeze nedeni açıklayıcı olmalıdır"
            )

        item = FreezeWindow(
            freeze_id=freeze_id,
            tenant_id=tenant_id,
            starts_at=starts_at,
            ends_at=ends_at,
            reason=reason,
            emergency_bypass_allowed=(
                emergency_bypass_allowed
            ),
            enabled=True,
            created_by=created_by,
            created_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_freeze(item)

    def approve(
        self,
        *,
        approval_id: str,
        tenant_id: str,
        release_id: str,
        role: str,
        actor: str,
        decision: str,
        comment: str,
        now: int | None = None,
    ) -> DeploymentApproval:
        normalized = decision.upper()
        if normalized not in {"APPROVED", "REJECTED"}:
            raise DeploymentSafetyValidationError(
                "Approval kararı APPROVED veya REJECTED olmalıdır"
            )
        if len(comment.strip()) < 3:
            raise DeploymentSafetyValidationError(
                "Approval açıklaması gereklidir"
            )

        item = DeploymentApproval(
            approval_id=approval_id,
            tenant_id=tenant_id,
            release_id=release_id,
            role=role.lower(),
            actor=actor,
            decision=normalized,
            comment=comment,
            decided_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_approval(item)

    def calculate_risk(
        self,
        *,
        tenant_id: str,
        release_id: str,
        plan_id: str,
        verification_session_id: str,
        changed_files: int,
        affected_services: int,
        now: int | None = None,
    ) -> DeploymentRiskSnapshot:
        if changed_files < 0 or affected_services < 0:
            raise DeploymentSafetyValidationError(
                "Change metrikleri negatif olamaz"
            )

        reliability = (
            self.reliability_service.reliability_score(
                tenant_id=tenant_id,
                now=now,
            )
        )
        rollout = (
            self.progressive_delivery_service
            .repository.get_state(plan_id)
        )
        verification = (
            self.deployment_verification_service
            .repository.get_session(
                verification_session_id
            )
        )
        if rollout is None:
            raise KeyError(
                "Progressive delivery state bulunamadı"
            )
        if verification is None:
            raise KeyError(
                "Verification session bulunamadı"
            )

        score = 0
        reasons = []

        reliability_score = int(
            reliability["score"]
        )
        warning = int(
            reliability.get("warning_slos", 0)
        )
        critical = int(
            reliability.get("critical_slos", 0)
        )

        if reliability_score < 70:
            penalty = min(
                35,
                70 - reliability_score,
            )
            score += penalty
            reasons.append(
                "Düşük reliability score"
            )
        if warning:
            score += min(20, warning * 10)
            reasons.append("Warning SLO mevcut")
        if critical:
            score += min(40, critical * 20)
            reasons.append("Critical SLO mevcut")
        if rollout.status != "COMPLETED":
            score += 20
            reasons.append(
                "Rollout tamamlanmamış"
            )
        if verification.status != "VERIFIED":
            score += 25
            reasons.append(
                "Deployment doğrulanmamış"
            )
        if changed_files > 100:
            score += 15
            reasons.append(
                "Değişiklik kapsamı geniş"
            )
        elif changed_files > 30:
            score += 8
            reasons.append(
                "Değişiklik kapsamı orta"
            )
        if affected_services > 5:
            score += 15
            reasons.append(
                "Çok sayıda servis etkileniyor"
            )
        elif affected_services > 2:
            score += 8
            reasons.append(
                "Birden fazla servis etkileniyor"
            )

        score = min(100, score)
        level = (
            "LOW"
            if score < 25
            else "MEDIUM"
            if score < 50
            else "HIGH"
            if score < 75
            else "CRITICAL"
        )

        snapshot = DeploymentRiskSnapshot(
            release_id=release_id,
            tenant_id=tenant_id,
            reliability_score=reliability_score,
            warning_slos=warning,
            critical_slos=critical,
            rollout_status=rollout.status,
            verification_status=verification.status,
            changed_files=changed_files,
            affected_services=affected_services,
            risk_score=score,
            risk_level=level,
            reasons=tuple(reasons),
            calculated_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_risk(snapshot)

    def evaluate(
        self,
        *,
        decision_id: str,
        tenant_id: str,
        release_id: str,
        emergency: bool = False,
        override_actor: str | None = None,
        override_reason: str | None = None,
        required_roles: tuple[str, ...] | None = None,
        now: int | None = None,
    ) -> DeploymentSafetyDecision:
        current = int(
            now if now is not None
            else time.time()
        )
        risk = self.repository.get_risk(
            tenant_id=tenant_id,
            release_id=release_id,
        )
        if risk is None:
            raise KeyError(
                "Deployment risk snapshot bulunamadı"
            )

        required = (
            required_roles
            or self.DEFAULT_APPROVAL_ROLES
        )
        normalized_required = tuple(
            sorted(set(role.lower() for role in required))
        )
        approvals = self.repository.list_approvals(
            tenant_id=tenant_id,
            release_id=release_id,
        )
        rejected = [
            item
            for item in approvals
            if item.decision == "REJECTED"
        ]
        approved_roles = tuple(
            sorted({
                item.role
                for item in approvals
                if item.decision == "APPROVED"
            })
        )

        freeze = self.repository.active_freeze(
            tenant_id=tenant_id,
            now=current,
        )

        blockers = []
        if rejected:
            blockers.append(
                "Release için reddedilmiş approval mevcut"
            )
        missing = tuple(
            role
            for role in normalized_required
            if role not in approved_roles
        )
        if missing:
            blockers.append(
                "Eksik approval rolleri: "
                + ", ".join(missing)
            )
        if risk.risk_level in {"HIGH", "CRITICAL"}:
            blockers.append(
                f"Deployment risk seviyesi {risk.risk_level}"
            )
        if freeze is not None:
            if not (
                emergency
                and freeze.emergency_bypass_allowed
            ):
                blockers.append(
                    f"Aktif production freeze: {freeze.reason}"
                )

        overridden = override_actor is not None
        if overridden:
            if not override_reason or len(
                override_reason.strip()
            ) < 8:
                raise DeploymentSafetyValidationError(
                    "Override için ayrıntılı neden gereklidir"
                )

        allowed = not blockers or overridden
        status = (
            "ALLOWED"
            if allowed and not overridden
            else "OVERRIDDEN"
            if overridden
            else "BLOCKED"
        )
        reason = (
            "Deployment safety gate başarıyla geçti"
            if not blockers
            else "Deployment safety gate override edildi"
            if overridden
            else "; ".join(blockers)
        )

        decision = DeploymentSafetyDecision(
            decision_id=decision_id,
            tenant_id=tenant_id,
            release_id=release_id,
            allowed=allowed,
            status=status,
            reason=reason,
            emergency=emergency,
            override_actor=override_actor,
            override_reason=override_reason,
            risk_score=risk.risk_score,
            freeze_id=(
                freeze.freeze_id
                if freeze is not None
                else None
            ),
            approvals_required=normalized_required,
            approvals_received=approved_roles,
            decided_at=current,
        )
        return self.repository.save_decision(decision)

    def timeline(
        self,
        *,
        tenant_id: str,
        release_id: str,
    ) -> tuple[dict, ...]:
        entries = []

        for approval in self.repository.list_approvals(
            tenant_id=tenant_id,
            release_id=release_id,
        ):
            entries.append({
                "type": "APPROVAL",
                "at": approval.decided_at,
                "status": approval.decision,
                "actor": approval.actor,
                "detail": (
                    f"{approval.role}: "
                    f"{approval.comment}"
                ),
            })

        risk = self.repository.get_risk(
            tenant_id=tenant_id,
            release_id=release_id,
        )
        if risk is not None:
            entries.append({
                "type": "RISK",
                "at": risk.calculated_at,
                "status": risk.risk_level,
                "actor": None,
                "detail": (
                    f"Risk score={risk.risk_score}"
                ),
            })

        for decision in self.repository.list_decisions(
            tenant_id,
            limit=1000,
        ):
            if decision.release_id != release_id:
                continue
            entries.append({
                "type": "SAFETY_DECISION",
                "at": decision.decided_at,
                "status": decision.status,
                "actor": decision.override_actor,
                "detail": decision.reason,
            })

        entries.sort(
            key=lambda item: (
                item["at"],
                item["type"],
            )
        )
        return tuple(entries)
