import pytest

from apps.api.app.reliability_management import (
    RedisReliabilityRepository,
    ReliabilityManagementService,
    ReliabilityValidationError,
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


def service():
    return ReliabilityManagementService(
        repository=RedisReliabilityRepository(
            Redis()
        )
    )


def test_invalid_slo_target_is_rejected():
    with pytest.raises(ReliabilityValidationError):
        service().create_slo(
            slo_id="x",
            tenant_id="t",
            service="api",
            indicator="availability",
            target=1.0,
            window_seconds=3600,
        )


def test_invalid_observation_is_rejected():
    item = service()
    item.create_slo(
        slo_id="x",
        tenant_id="t",
        service="api",
        indicator="availability",
        target=0.99,
        window_seconds=3600,
    )

    with pytest.raises(ReliabilityValidationError):
        item.record(
            observation_id="o1",
            slo_id="x",
            good_events=101,
            total_events=100,
        )
