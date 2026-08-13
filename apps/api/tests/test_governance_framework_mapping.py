from apps.api.app.governance import (
    GovernanceService,
    RedisGovernanceRepository,
)
from apps.api.app.governance_exceptions import (
    GovernanceExceptionService,
    RedisGovernanceExceptionRepository,
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


def test_iso_framework_coverage():
    redis = Redis()
    governance = GovernanceService(
        repository=RedisGovernanceRepository(
            redis,
            prefix="gov",
        )
    )
    service = GovernanceExceptionService(
        repository=RedisGovernanceExceptionRepository(
            redis,
            prefix="ex",
        ),
        governance_service=governance,
    )

    governance.create_control(
        control_id="c1",
        tenant_id="t1",
        name="Deployment evidence",
        policy_ids=("p1",),
        required_evidence_types=("VERIFICATION",),
        now=100,
    )
    service.create_mapping(
        mapping_id="m1",
        tenant_id="t1",
        framework="ISO27001",
        framework_control="A.8.32",
        governance_control_id="c1",
        evidence_types=("verification",),
        now=101,
    )
    governance.collect_evidence(
        evidence_id="e1",
        tenant_id="t1",
        evidence_type="verification",
        source_system="deployment",
        source_reference="v1",
        metadata={"status": "VERIFIED"},
        now=102,
    )

    report = service.framework_report(
        tenant_id="t1",
        framework="ISO27001",
        now=103,
    )

    assert report["coverage_percent"] == 100.0
    assert report["gaps"] == []
