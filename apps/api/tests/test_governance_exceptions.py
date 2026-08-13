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


def build():
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
    return governance, service


def test_exception_and_risk_acceptance():
    governance, service = build()
    governance.create_policy(
        policy_id="p1",
        tenant_id="t1",
        name="Policy",
        category="security",
        scope="production",
        owner="sec",
        rules=("encrypted=true",),
        now=100,
    )

    exception = service.create_exception(
        exception_id="x1",
        tenant_id="t1",
        policy_id="p1",
        resource="service:api",
        reason="Legacy dependency migration",
        risk_level="high",
        approved_by="sec-user",
        starts_at=100,
        expires_at=200,
        now=90,
    )
    acceptance = service.accept_risk(
        acceptance_id="a1",
        tenant_id="t1",
        exception_id="x1",
        risk_owner="risk-owner",
        residual_risk="medium",
        compensating_controls=("monitoring",),
        decision="accepted",
        now=101,
    )
    updated = service.exception_status(
        exception_id="x1",
        now=110,
    )

    assert exception.status == "ACTIVE"
    assert acceptance.decision == "ACCEPTED"
    assert updated.status == "APPROVED"


def test_exception_expires():
    governance, service = build()
    governance.create_policy(
        policy_id="p1",
        tenant_id="t1",
        name="Policy",
        category="security",
        scope="production",
        owner="sec",
        rules=("encrypted=true",),
        now=100,
    )
    service.create_exception(
        exception_id="x1",
        tenant_id="t1",
        policy_id="p1",
        resource="service:api",
        reason="Temporary migration window",
        risk_level="medium",
        approved_by="sec-user",
        starts_at=100,
        expires_at=120,
        now=90,
    )

    expired = service.exception_status(
        exception_id="x1",
        now=121,
    )

    assert expired.status == "EXPIRED"
