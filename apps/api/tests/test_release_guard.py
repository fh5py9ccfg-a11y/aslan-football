import pytest

from apps.api.app.release_guard import (
    RedisReleaseGuardRepository,
    ReleaseGuardService,
    ReleaseGuardValidationError,
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


class Reliability:
    def __init__(
        self,
        *,
        score=100,
        warning=0,
        critical=0,
    ):
        self.result = {
            "score": score,
            "status": (
                "HEALTHY"
                if score >= 70
                else "AT_RISK"
            ),
            "warning_slos": warning,
            "critical_slos": critical,
        }

    def reliability_score(self, **kwargs):
        return self.result


def build(reliability):
    return ReleaseGuardService(
        repository=RedisReleaseGuardRepository(
            Redis(),
            prefix="guard",
        ),
        reliability_service=reliability,
    )


def test_healthy_release_is_allowed():
    service = build(Reliability(score=90))
    service.create_policy(
        policy_id="p1",
        tenant_id="tenant-a",
        now=100,
    )

    decision = service.evaluate(
        decision_id="d1",
        tenant_id="tenant-a",
        release_id="r1",
        now=110,
    )

    assert decision.allowed is True
    assert decision.overridden is False


def test_critical_budget_blocks_release():
    service = build(
        Reliability(
            score=20,
            critical=1,
        )
    )
    service.create_policy(
        policy_id="p1",
        tenant_id="tenant-a",
        now=100,
    )

    decision = service.evaluate(
        decision_id="d1",
        tenant_id="tenant-a",
        release_id="r1",
        now=110,
    )

    assert decision.allowed is False
    assert decision.critical_slos == 1


def test_authorized_override_allows_release():
    service = build(
        Reliability(
            score=20,
            critical=1,
        )
    )
    service.create_policy(
        policy_id="p1",
        tenant_id="tenant-a",
        now=100,
    )

    decision = service.evaluate(
        decision_id="d1",
        tenant_id="tenant-a",
        release_id="r1",
        override_actor="ops-user",
        override_reason="Emergency security patch",
        now=110,
    )

    assert decision.allowed is True
    assert decision.overridden is True
    assert decision.override_actor == "ops-user"


def test_override_reason_is_required():
    service = build(Reliability(score=20))
    service.create_policy(
        policy_id="p1",
        tenant_id="tenant-a",
        now=100,
    )

    with pytest.raises(ReleaseGuardValidationError):
        service.evaluate(
            decision_id="d1",
            tenant_id="tenant-a",
            release_id="r1",
            override_actor="ops-user",
            override_reason="x",
            now=110,
        )
