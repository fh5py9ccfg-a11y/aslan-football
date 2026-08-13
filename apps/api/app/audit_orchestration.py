from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class AuditPlan:
    audit_id: str
    tenant_id: str
    framework: str
    scope: str
    lead_auditor: str
    starts_at: int
    ends_at: int
    status: str
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class EvidenceRequest:
    request_id: str
    audit_id: str
    tenant_id: str
    control_id: str
    evidence_type: str
    assignee: str
    due_at: int
    status: str
    evidence_id: str | None
    note: str
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class AuditFinding:
    finding_id: str
    audit_id: str
    tenant_id: str
    control_id: str
    severity: str
    title: str
    detail: str
    owner: str
    status: str
    due_at: int
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class AuditReadinessReport:
    audit_id: str
    tenant_id: str
    total_requests: int
    fulfilled_requests: int
    overdue_requests: int
    open_findings: int
    critical_findings: int
    readiness_score: int
    status: str
    gaps: tuple[str, ...]
    generated_at: int


class AuditOrchestrationError(RuntimeError):
    pass


class AuditOrchestrationValidationError(ValueError):
    pass


class RedisAuditOrchestrationRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:audit-orchestration",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_audit(self, audit: AuditPlan) -> AuditPlan:
        self.client.setex(
            self._audit_key(audit.audit_id),
            self.ttl_seconds,
            json.dumps(audit.__dict__, ensure_ascii=False, separators=(",", ":")),
        )
        self.client.sadd(
            self._tenant_audit_index(audit.tenant_id),
            audit.audit_id,
        )
        return audit

    def get_audit(self, audit_id: str) -> AuditPlan | None:
        payload = self.client.get(self._audit_key(audit_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return AuditPlan(**json.loads(payload))

    def list_audits(self, tenant_id: str) -> tuple[AuditPlan, ...]:
        items = []
        for audit_id in self.client.smembers(
            self._tenant_audit_index(tenant_id)
        ):
            if isinstance(audit_id, bytes):
                audit_id = audit_id.decode("utf-8")
            item = self.get_audit(str(audit_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.starts_at)
        return tuple(items)

    def save_request(self, item: EvidenceRequest) -> EvidenceRequest:
        self.client.setex(
            self._request_key(item.request_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False, separators=(",", ":")),
        )
        self.client.sadd(
            self._audit_request_index(item.audit_id),
            item.request_id,
        )
        return item

    def get_request(self, request_id: str) -> EvidenceRequest | None:
        payload = self.client.get(self._request_key(request_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return EvidenceRequest(**json.loads(payload))

    def list_requests(self, audit_id: str) -> tuple[EvidenceRequest, ...]:
        items = []
        for request_id in self.client.smembers(
            self._audit_request_index(audit_id)
        ):
            if isinstance(request_id, bytes):
                request_id = request_id.decode("utf-8")
            item = self.get_request(str(request_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def save_finding(self, item: AuditFinding) -> AuditFinding:
        self.client.setex(
            self._finding_key(item.finding_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False, separators=(",", ":")),
        )
        self.client.sadd(
            self._audit_finding_index(item.audit_id),
            item.finding_id,
        )
        return item

    def get_finding(self, finding_id: str) -> AuditFinding | None:
        payload = self.client.get(self._finding_key(finding_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return AuditFinding(**json.loads(payload))

    def list_findings(self, audit_id: str) -> tuple[AuditFinding, ...]:
        items = []
        for finding_id in self.client.smembers(
            self._audit_finding_index(audit_id)
        ):
            if isinstance(finding_id, bytes):
                finding_id = finding_id.decode("utf-8")
            item = self.get_finding(str(finding_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def _audit_key(self, audit_id: str) -> str:
        return f"{self.prefix}:audit:{audit_id}"

    def _tenant_audit_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:audits:{tenant_id}"

    def _request_key(self, request_id: str) -> str:
        return f"{self.prefix}:request:{request_id}"

    def _audit_request_index(self, audit_id: str) -> str:
        return f"{self.prefix}:requests:{audit_id}"

    def _finding_key(self, finding_id: str) -> str:
        return f"{self.prefix}:finding:{finding_id}"

    def _audit_finding_index(self, audit_id: str) -> str:
        return f"{self.prefix}:findings:{audit_id}"


class AuditOrchestrationService:
    VALID_FRAMEWORKS = {"ISO27001", "SOC2", "KVKK", "GDPR", "INTERNAL"}
    VALID_SEVERITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

    def __init__(
        self,
        *,
        repository,
        governance_service,
    ):
        self.repository = repository
        self.governance_service = governance_service

    def create_audit(
        self,
        *,
        audit_id: str,
        tenant_id: str,
        framework: str,
        scope: str,
        lead_auditor: str,
        starts_at: int,
        ends_at: int,
        now: int | None = None,
    ) -> AuditPlan:
        normalized = framework.upper()
        if normalized not in self.VALID_FRAMEWORKS:
            raise AuditOrchestrationValidationError(
                "Desteklenmeyen audit framework"
            )
        if ends_at <= starts_at:
            raise AuditOrchestrationValidationError(
                "Audit bitiş zamanı başlangıçtan büyük olmalıdır"
            )
        current = int(now if now is not None else time.time())
        audit = AuditPlan(
            audit_id=audit_id,
            tenant_id=tenant_id,
            framework=normalized,
            scope=scope,
            lead_auditor=lead_auditor,
            starts_at=starts_at,
            ends_at=ends_at,
            status="PLANNED",
            created_at=current,
            updated_at=current,
        )
        return self.repository.save_audit(audit)

    def transition_audit(
        self,
        *,
        audit_id: str,
        target_status: str,
        now: int | None = None,
    ) -> AuditPlan:
        audit = self._required_audit(audit_id)
        transitions = {
            "PLANNED": {"IN_PROGRESS", "CANCELLED"},
            "IN_PROGRESS": {"REVIEW", "CANCELLED"},
            "REVIEW": {"COMPLETED", "IN_PROGRESS"},
            "COMPLETED": set(),
            "CANCELLED": set(),
        }
        target = target_status.upper()
        if target not in transitions[audit.status]:
            raise AuditOrchestrationError(
                f"Geçersiz audit geçişi: {audit.status} -> {target}"
            )
        updated = AuditPlan(
            **{
                **audit.__dict__,
                "status": target,
                "updated_at": int(now if now is not None else time.time()),
            }
        )
        return self.repository.save_audit(updated)

    def create_evidence_request(
        self,
        *,
        request_id: str,
        audit_id: str,
        control_id: str,
        evidence_type: str,
        assignee: str,
        due_at: int,
        note: str,
        now: int | None = None,
    ) -> EvidenceRequest:
        audit = self._required_audit(audit_id)
        controls = self.governance_service.repository.list_controls(
            audit.tenant_id
        )
        if not any(item.control_id == control_id for item in controls):
            raise KeyError("Governance control bulunamadı")
        current = int(now if now is not None else time.time())
        if due_at <= current:
            raise AuditOrchestrationValidationError(
                "Evidence request due_at gelecekte olmalıdır"
            )
        item = EvidenceRequest(
            request_id=request_id,
            audit_id=audit_id,
            tenant_id=audit.tenant_id,
            control_id=control_id,
            evidence_type=evidence_type.upper(),
            assignee=assignee,
            due_at=due_at,
            status="OPEN",
            evidence_id=None,
            note=note,
            created_at=current,
            updated_at=current,
        )
        return self.repository.save_request(item)

    def fulfill_evidence_request(
        self,
        *,
        request_id: str,
        evidence_id: str,
        now: int | None = None,
    ) -> EvidenceRequest:
        item = self._required_request(request_id)
        evidence = self.governance_service.repository.list_evidence(
            item.tenant_id
        )
        if not any(ev.evidence_id == evidence_id for ev in evidence):
            raise KeyError("Governance evidence bulunamadı")
        if item.status not in {"OPEN", "OVERDUE"}:
            raise AuditOrchestrationError(
                "Evidence request fulfill edilemez"
            )
        updated = EvidenceRequest(
            **{
                **item.__dict__,
                "status": "FULFILLED",
                "evidence_id": evidence_id,
                "updated_at": int(now if now is not None else time.time()),
            }
        )
        return self.repository.save_request(updated)

    def refresh_request_status(
        self,
        *,
        request_id: str,
        now: int | None = None,
    ) -> EvidenceRequest:
        item = self._required_request(request_id)
        current = int(now if now is not None else time.time())
        if item.status == "OPEN" and current > item.due_at:
            item = EvidenceRequest(
                **{
                    **item.__dict__,
                    "status": "OVERDUE",
                    "updated_at": current,
                }
            )
            self.repository.save_request(item)
        return item

    def create_finding(
        self,
        *,
        finding_id: str,
        audit_id: str,
        control_id: str,
        severity: str,
        title: str,
        detail: str,
        owner: str,
        due_at: int,
        now: int | None = None,
    ) -> AuditFinding:
        audit = self._required_audit(audit_id)
        normalized = severity.upper()
        if normalized not in self.VALID_SEVERITIES:
            raise AuditOrchestrationValidationError(
                "Geçersiz finding severity"
            )
        current = int(now if now is not None else time.time())
        if due_at <= current:
            raise AuditOrchestrationValidationError(
                "Finding due_at gelecekte olmalıdır"
            )
        item = AuditFinding(
            finding_id=finding_id,
            audit_id=audit_id,
            tenant_id=audit.tenant_id,
            control_id=control_id,
            severity=normalized,
            title=title,
            detail=detail,
            owner=owner,
            status="OPEN",
            due_at=due_at,
            created_at=current,
            updated_at=current,
        )
        return self.repository.save_finding(item)

    def transition_finding(
        self,
        *,
        finding_id: str,
        target_status: str,
        now: int | None = None,
    ) -> AuditFinding:
        item = self._required_finding(finding_id)
        transitions = {
            "OPEN": {"IN_REMEDIATION", "ACCEPTED"},
            "IN_REMEDIATION": {"RESOLVED", "ACCEPTED"},
            "RESOLVED": set(),
            "ACCEPTED": set(),
        }
        target = target_status.upper()
        if target not in transitions[item.status]:
            raise AuditOrchestrationError(
                f"Geçersiz finding geçişi: {item.status} -> {target}"
            )
        updated = AuditFinding(
            **{
                **item.__dict__,
                "status": target,
                "updated_at": int(now if now is not None else time.time()),
            }
        )
        return self.repository.save_finding(updated)

    def readiness_report(
        self,
        *,
        audit_id: str,
        now: int | None = None,
    ) -> AuditReadinessReport:
        audit = self._required_audit(audit_id)
        current = int(now if now is not None else time.time())
        requests = [
            self.refresh_request_status(
                request_id=item.request_id,
                now=current,
            )
            for item in self.repository.list_requests(audit_id)
        ]
        findings = self.repository.list_findings(audit_id)

        fulfilled = sum(
            1 for item in requests if item.status == "FULFILLED"
        )
        overdue = sum(
            1 for item in requests if item.status == "OVERDUE"
        )
        open_findings = sum(
            1
            for item in findings
            if item.status in {"OPEN", "IN_REMEDIATION"}
        )
        critical = sum(
            1
            for item in findings
            if item.severity == "CRITICAL"
            and item.status not in {"RESOLVED", "ACCEPTED"}
        )

        total = len(requests)
        request_score = (
            100
            if total == 0
            else round(fulfilled / total * 100)
        )
        penalty = min(
            100,
            overdue * 15 + open_findings * 10 + critical * 25,
        )
        score = max(0, request_score - penalty)

        status = (
            "READY"
            if score >= 80 and critical == 0
            else "PARTIAL"
            if score >= 50
            else "NOT_READY"
        )

        gaps = []
        if overdue:
            gaps.append(f"Overdue evidence request={overdue}")
        if open_findings:
            gaps.append(f"Open finding={open_findings}")
        if critical:
            gaps.append(f"Critical finding={critical}")

        return AuditReadinessReport(
            audit_id=audit_id,
            tenant_id=audit.tenant_id,
            total_requests=total,
            fulfilled_requests=fulfilled,
            overdue_requests=overdue,
            open_findings=open_findings,
            critical_findings=critical,
            readiness_score=score,
            status=status,
            gaps=tuple(gaps),
            generated_at=current,
        )

    def timeline(
        self,
        *,
        audit_id: str,
    ) -> tuple[dict, ...]:
        audit = self._required_audit(audit_id)
        items = [{
            "type": "AUDIT",
            "at": audit.updated_at,
            "status": audit.status,
            "resource": audit.audit_id,
            "detail": audit.scope,
        }]
        for request in self.repository.list_requests(audit_id):
            items.append({
                "type": "EVIDENCE_REQUEST",
                "at": request.updated_at,
                "status": request.status,
                "resource": request.control_id,
                "detail": request.evidence_type,
            })
        for finding in self.repository.list_findings(audit_id):
            items.append({
                "type": "FINDING",
                "at": finding.updated_at,
                "status": finding.status,
                "resource": finding.control_id,
                "detail": finding.title,
            })
        items.sort(key=lambda item: (item["at"], item["type"]))
        return tuple(items)

    def _required_audit(self, audit_id: str) -> AuditPlan:
        item = self.repository.get_audit(audit_id)
        if item is None:
            raise KeyError("Audit plan bulunamadı")
        return item

    def _required_request(self, request_id: str) -> EvidenceRequest:
        item = self.repository.get_request(request_id)
        if item is None:
            raise KeyError("Evidence request bulunamadı")
        return item

    def _required_finding(self, finding_id: str) -> AuditFinding:
        item = self.repository.get_finding(finding_id)
        if item is None:
            raise KeyError("Audit finding bulunamadı")
        return item
