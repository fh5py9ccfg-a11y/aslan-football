from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class ComplianceSnapshot:
    snapshot_id: str
    tenant_id: str
    governance_score: int
    framework_score: int
    exception_health_score: int
    evidence_score: int
    overall_score: int
    status: str
    gaps: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class ComplianceDriftEvent:
    drift_id: str
    tenant_id: str
    drift_type: str
    severity: str
    resource: str
    detail: str
    previous_value: str | None
    current_value: str
    detected_at: int


@dataclass(frozen=True)
class RemediationAction:
    action_id: str
    tenant_id: str
    drift_id: str
    action_type: str
    assignee: str
    status: str
    due_at: int
    detail: str
    created_at: int
    updated_at: int


class ContinuousComplianceError(RuntimeError):
    pass


class ContinuousComplianceValidationError(ValueError):
    pass


class RedisContinuousComplianceRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:continuous-compliance",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_snapshot(
        self,
        snapshot: ComplianceSnapshot,
    ) -> ComplianceSnapshot:
        payload = {
            **snapshot.__dict__,
            "gaps": list(snapshot.gaps),
        }
        self.client.setex(
            self._snapshot_key(snapshot.snapshot_id),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._snapshot_index(snapshot.tenant_id),
            snapshot.snapshot_id,
        )
        return snapshot

    def latest_snapshot(
        self,
        tenant_id: str,
    ) -> ComplianceSnapshot | None:
        items = self.list_snapshots(tenant_id)
        return items[-1] if items else None

    def list_snapshots(
        self,
        tenant_id: str,
    ) -> tuple[ComplianceSnapshot, ...]:
        items = []
        for snapshot_id in self.client.smembers(
            self._snapshot_index(tenant_id)
        ):
            if isinstance(snapshot_id, bytes):
                snapshot_id = snapshot_id.decode("utf-8")
            payload = self.client.get(
                self._snapshot_key(str(snapshot_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            data["gaps"] = tuple(data["gaps"])
            items.append(ComplianceSnapshot(**data))
        items.sort(key=lambda item: item.generated_at)
        return tuple(items)

    def save_drift(
        self,
        drift: ComplianceDriftEvent,
    ) -> ComplianceDriftEvent:
        self.client.setex(
            self._drift_key(drift.drift_id),
            self.ttl_seconds,
            json.dumps(
                drift.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._drift_index(drift.tenant_id),
            drift.drift_id,
        )
        return drift

    def list_drifts(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
    ) -> tuple[ComplianceDriftEvent, ...]:
        items = []
        for drift_id in self.client.smembers(
            self._drift_index(tenant_id)
        ):
            if isinstance(drift_id, bytes):
                drift_id = drift_id.decode("utf-8")
            payload = self.client.get(
                self._drift_key(str(drift_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                ComplianceDriftEvent(**json.loads(payload))
            )
        items.sort(
            key=lambda item: item.detected_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def get_drift(
        self,
        drift_id: str,
    ) -> ComplianceDriftEvent | None:
        payload = self.client.get(
            self._drift_key(drift_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ComplianceDriftEvent(
            **json.loads(payload)
        )

    def save_action(
        self,
        action: RemediationAction,
    ) -> RemediationAction:
        self.client.setex(
            self._action_key(action.action_id),
            self.ttl_seconds,
            json.dumps(
                action.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._action_index(action.tenant_id),
            action.action_id,
        )
        return action

    def get_action(
        self,
        action_id: str,
    ) -> RemediationAction | None:
        payload = self.client.get(
            self._action_key(action_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return RemediationAction(
            **json.loads(payload)
        )

    def list_actions(
        self,
        tenant_id: str,
    ) -> tuple[RemediationAction, ...]:
        items = []
        for action_id in self.client.smembers(
            self._action_index(tenant_id)
        ):
            if isinstance(action_id, bytes):
                action_id = action_id.decode("utf-8")
            action = self.get_action(str(action_id))
            if action is not None:
                items.append(action)
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def _snapshot_key(self, snapshot_id: str) -> str:
        return f"{self.prefix}:snapshot:{snapshot_id}"

    def _snapshot_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:snapshots:{tenant_id}"

    def _drift_key(self, drift_id: str) -> str:
        return f"{self.prefix}:drift:{drift_id}"

    def _drift_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:drifts:{tenant_id}"

    def _action_key(self, action_id: str) -> str:
        return f"{self.prefix}:action:{action_id}"

    def _action_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:actions:{tenant_id}"


class ContinuousComplianceService:
    FRAMEWORKS = (
        "ISO27001",
        "SOC2",
        "KVKK",
        "GDPR",
    )

    def __init__(
        self,
        *,
        repository,
        governance_service,
        governance_exception_service,
    ):
        self.repository = repository
        self.governance_service = governance_service
        self.governance_exception_service = (
            governance_exception_service
        )

    def monitor(
        self,
        *,
        snapshot_id: str,
        tenant_id: str,
        now: int | None = None,
    ) -> ComplianceSnapshot:
        current = int(
            now if now is not None
            else time.time()
        )
        previous = self.repository.latest_snapshot(
            tenant_id
        )

        governance = (
            self.governance_service.compliance_report(
                tenant_id=tenant_id,
                now=current,
            )
        )

        framework_reports = [
            self.governance_exception_service
            .framework_report(
                tenant_id=tenant_id,
                framework=framework,
                now=current,
            )
            for framework in self.FRAMEWORKS
        ]
        mapped_reports = [
            item
            for item in framework_reports
            if item["total_controls"] > 0
        ]
        framework_score = (
            100
            if not mapped_reports
            else round(
                sum(
                    item["coverage_percent"]
                    for item in mapped_reports
                )
                / len(mapped_reports)
            )
        )

        exceptions = (
            self.governance_exception_service
            .repository.list_exceptions(tenant_id)
        )
        active = 0
        expired = 0
        rejected = 0
        for item in exceptions:
            current_item = (
                self.governance_exception_service
                .exception_status(
                    exception_id=item.exception_id,
                    now=current,
                )
            )
            if current_item.status in {
                "ACTIVE",
                "APPROVED",
            }:
                active += 1
            elif current_item.status == "EXPIRED":
                expired += 1
            elif current_item.status == "REJECTED":
                rejected += 1

        exception_penalty = min(
            100,
            active * 10 + expired * 20 + rejected * 25,
        )
        exception_health = 100 - exception_penalty

        governance_score = round(
            (
                governance.policy_coverage_percent
                + (
                    100
                    if governance.total_controls == 0
                    else governance.compliant_controls
                    / governance.total_controls
                    * 100
                )
            )
            / 2
        )
        evidence_score = round(
            governance.evidence_coverage_percent
        )

        overall = round(
            governance_score * 0.35
            + framework_score * 0.25
            + exception_health * 0.20
            + evidence_score * 0.20
        )
        status = (
            "HEALTHY"
            if overall >= 80
            else "AT_RISK"
            if overall >= 60
            else "NON_COMPLIANT"
        )

        gaps = list(governance.gaps)
        for report in mapped_reports:
            gaps.extend(
                f"{report['framework']}: {item}"
                for item in report["gaps"]
            )
        if expired:
            gaps.append(
                f"Expired exception sayısı={expired}"
            )
        if rejected:
            gaps.append(
                f"Rejected exception sayısı={rejected}"
            )

        snapshot = ComplianceSnapshot(
            snapshot_id=snapshot_id,
            tenant_id=tenant_id,
            governance_score=governance_score,
            framework_score=framework_score,
            exception_health_score=(
                exception_health
            ),
            evidence_score=evidence_score,
            overall_score=overall,
            status=status,
            gaps=tuple(gaps),
            generated_at=current,
        )
        self.repository.save_snapshot(snapshot)

        if previous is not None:
            self._detect_drift(
                tenant_id=tenant_id,
                previous=previous,
                current=snapshot,
                now=current,
            )
        return snapshot

    def _detect_drift(
        self,
        *,
        tenant_id: str,
        previous: ComplianceSnapshot,
        current: ComplianceSnapshot,
        now: int,
    ) -> None:
        events = []

        if current.overall_score < previous.overall_score:
            delta = (
                previous.overall_score
                - current.overall_score
            )
            severity = (
                "CRITICAL"
                if delta >= 20
                else "HIGH"
                if delta >= 10
                else "MEDIUM"
            )
            events.append(
                ComplianceDriftEvent(
                    drift_id=(
                        f"{current.snapshot_id}:score"
                    ),
                    tenant_id=tenant_id,
                    drift_type="SCORE_DROP",
                    severity=severity,
                    resource="tenant",
                    detail=(
                        f"Compliance score {delta} puan düştü"
                    ),
                    previous_value=str(
                        previous.overall_score
                    ),
                    current_value=str(
                        current.overall_score
                    ),
                    detected_at=now,
                )
            )

        if current.evidence_score < previous.evidence_score:
            events.append(
                ComplianceDriftEvent(
                    drift_id=(
                        f"{current.snapshot_id}:evidence"
                    ),
                    tenant_id=tenant_id,
                    drift_type="EVIDENCE_COVERAGE_DROP",
                    severity="HIGH",
                    resource="evidence-registry",
                    detail=(
                        "Evidence coverage geriledi"
                    ),
                    previous_value=str(
                        previous.evidence_score
                    ),
                    current_value=str(
                        current.evidence_score
                    ),
                    detected_at=now,
                )
            )

        new_gaps = set(current.gaps) - set(previous.gaps)
        for index, gap in enumerate(
            sorted(new_gaps),
            start=1,
        ):
            events.append(
                ComplianceDriftEvent(
                    drift_id=(
                        f"{current.snapshot_id}:gap:{index}"
                    ),
                    tenant_id=tenant_id,
                    drift_type="NEW_GAP",
                    severity="MEDIUM",
                    resource="compliance-report",
                    detail=gap,
                    previous_value=None,
                    current_value=gap,
                    detected_at=now,
                )
            )

        for event in events:
            self.repository.save_drift(event)

    def create_remediation(
        self,
        *,
        action_id: str,
        tenant_id: str,
        drift_id: str,
        action_type: str,
        assignee: str,
        due_at: int,
        detail: str,
        now: int | None = None,
    ) -> RemediationAction:
        drift = self.repository.get_drift(
            drift_id
        )
        if drift is None or drift.tenant_id != tenant_id:
            raise KeyError(
                "Compliance drift bulunamadı"
            )
        current = int(
            now if now is not None
            else time.time()
        )
        if due_at <= current:
            raise ContinuousComplianceValidationError(
                "Remediation due_at gelecekte olmalıdır"
            )
        if len(detail.strip()) < 5:
            raise ContinuousComplianceValidationError(
                "Remediation açıklaması gereklidir"
            )
        action = RemediationAction(
            action_id=action_id,
            tenant_id=tenant_id,
            drift_id=drift_id,
            action_type=action_type.upper(),
            assignee=assignee,
            status="OPEN",
            due_at=due_at,
            detail=detail,
            created_at=current,
            updated_at=current,
        )
        return self.repository.save_action(action)

    def transition_remediation(
        self,
        *,
        action_id: str,
        target_status: str,
        now: int | None = None,
    ) -> RemediationAction:
        action = self.repository.get_action(
            action_id
        )
        if action is None:
            raise KeyError(
                "Remediation action bulunamadı"
            )

        transitions = {
            "OPEN": {"IN_PROGRESS", "CANCELLED"},
            "IN_PROGRESS": {
                "RESOLVED",
                "CANCELLED",
            },
            "RESOLVED": set(),
            "CANCELLED": set(),
        }
        target = target_status.upper()
        if target not in transitions[action.status]:
            raise ContinuousComplianceError(
                f"Geçersiz remediation geçişi: "
                f"{action.status} -> {target}"
            )

        updated = RemediationAction(
            **{
                **action.__dict__,
                "status": target,
                "updated_at": int(
                    now if now is not None
                    else time.time()
                ),
            }
        )
        return self.repository.save_action(updated)

    def timeline(
        self,
        *,
        tenant_id: str,
    ) -> tuple[dict, ...]:
        items = []

        for snapshot in (
            self.repository.list_snapshots(
                tenant_id
            )
        ):
            items.append({
                "type": "SNAPSHOT",
                "at": snapshot.generated_at,
                "status": snapshot.status,
                "resource": tenant_id,
                "detail": (
                    f"overall={snapshot.overall_score}"
                ),
            })

        for drift in self.repository.list_drifts(
            tenant_id,
            limit=1000,
        ):
            items.append({
                "type": "DRIFT",
                "at": drift.detected_at,
                "status": drift.severity,
                "resource": drift.resource,
                "detail": drift.detail,
            })

        for action in self.repository.list_actions(
            tenant_id
        ):
            items.append({
                "type": "REMEDIATION",
                "at": action.updated_at,
                "status": action.status,
                "resource": action.drift_id,
                "detail": action.detail,
            })

        items.sort(
            key=lambda item: (
                item["at"],
                item["type"],
            )
        )
        return tuple(items)
