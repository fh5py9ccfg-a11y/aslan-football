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


class Governance:
    class repository:
        @staticmethod
        def list_controls(tenant_id):
            return ()


def test_critical_finding_reduces_readiness():
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
    service.create_finding(
        finding_id="f1",
        audit_id="a1",
        control_id="c1",
        severity="critical",
        title="Missing evidence",
        detail="Required evidence is unavailable",
        owner="ops",
        due_at=200,
        now=110,
    )

    report = service.readiness_report(
        audit_id="a1",
        now=120,
    )

    assert report.status == "PARTIAL"
    assert report.critical_findings == 1
    assert report.readiness_score == 65
