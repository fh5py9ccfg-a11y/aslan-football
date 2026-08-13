from apps.api.app.audit_orchestration import (
    AuditOrchestrationService,
    RedisAuditOrchestrationRepository,
)
from apps.api.app.governance import (
    GovernanceService,
    RedisGovernanceRepository,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


def build():
    redis = Redis()
    governance = GovernanceService(
        repository=RedisGovernanceRepository(
            redis,
            prefix="gov",
        )
    )
    audit = AuditOrchestrationService(
        repository=RedisAuditOrchestrationRepository(
            redis,
            prefix="audit",
        ),
        governance_service=governance,
    )
    return governance, audit


def test_audit_evidence_request_and_readiness():
    governance, audit = build()
    governance.create_control(
        control_id="c1",
        tenant_id="t1",
        name="Deployment verification",
        policy_ids=("p1",),
        required_evidence_types=("VERIFICATION",),
        now=100,
    )
    governance.collect_evidence(
        evidence_id="e1",
        tenant_id="t1",
        evidence_type="verification",
        source_system="deployment",
        source_reference="session:v1",
        metadata={"status": "VERIFIED"},
        now=101,
    )

    audit.create_audit(
        audit_id="a1",
        tenant_id="t1",
        framework="ISO27001",
        scope="production",
        lead_auditor="auditor",
        starts_at=100,
        ends_at=300,
        now=90,
    )
    audit.transition_audit(
        audit_id="a1",
        target_status="IN_PROGRESS",
        now=100,
    )
    audit.create_evidence_request(
        request_id="r1",
        audit_id="a1",
        control_id="c1",
        evidence_type="verification",
        assignee="ops",
        due_at=200,
        note="Provide evidence",
        now=110,
    )
    fulfilled = audit.fulfill_evidence_request(
        request_id="r1",
        evidence_id="e1",
        now=120,
    )
    report = audit.readiness_report(
        audit_id="a1",
        now=130,
    )

    assert fulfilled.status == "FULFILLED"
    assert report.status == "READY"
    assert report.readiness_score == 100
