import pytest

from apps.api.app.progressive_delivery import (
    ProgressiveDeliveryService,
    ProgressiveDeliveryValidationError,
    RedisProgressiveDeliveryRepository,
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
    def reliability_score(self, **kwargs):
        return {
            "score": 100,
            "status": "HEALTHY",
            "warning_slos": 0,
            "critical_slos": 0,
        }


class Guard:
    def evaluate(self, **kwargs):
        raise AssertionError


def service():
    return ProgressiveDeliveryService(
        repository=(
            RedisProgressiveDeliveryRepository(
                Redis()
            )
        ),
        reliability_service=Reliability(),
        release_guard_service=Guard(),
    )


def test_final_stage_must_be_one_hundred():
    with pytest.raises(
        ProgressiveDeliveryValidationError
    ):
        service().create_plan(
            plan_id="p1",
            tenant_id="t",
            release_id="r",
            stages=(10, 50),
        )


def test_stages_must_be_increasing():
    with pytest.raises(
        ProgressiveDeliveryValidationError
    ):
        service().create_plan(
            plan_id="p1",
            tenant_id="t",
            release_id="r",
            stages=(50, 10, 100),
        )
