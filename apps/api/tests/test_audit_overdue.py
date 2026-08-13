from apps.api.app.audit_orchestration import (
    AuditOrchestrationService,
    RedisAuditOrchestrationRepository,
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


class Control:
    control_id = "c1"


class Governance:
    class repository:
        @staticmethod
        def list_controls(tenant_id):
            return (Control(),)


def test_overdue_request_is_detected():
    service = AuditOrchestrationService(
        repository=RedisAuditOrchestrationRepository(
            Redis(),
            prefix="audit",
        ),
        governance_service=Governance(),
    )
    service.create_audit(
        audit_id="a1",
        tenant_id="t1",
        framework="INTERNAL",
        scope="platform",
        lead_auditor="auditor",
        starts_at=100,
        ends_at=300,
        now=90,
    )
    service.create_evidence_request(
        request_id="r1",
        audit_id="a1",
        control_id="c1",
        evidence_type="verification",
        assignee="ops",
        due_at=120,
        note="Provide evidence",
        now=100,
    )

    report = service.readiness_report(
        audit_id="a1",
        now=121,
    )

    assert report.overdue_requests == 1
    assert report.status == "NOT_READY"
