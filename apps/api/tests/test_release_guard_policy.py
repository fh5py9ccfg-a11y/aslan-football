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
    def reliability_score(self, **kwargs):
        return {
            "score": 100,
            "status": "HEALTHY",
            "warning_slos": 0,
            "critical_slos": 0,
        }


def test_invalid_minimum_score_is_rejected():
    service = ReleaseGuardService(
        repository=RedisReleaseGuardRepository(
            Redis()
        ),
        reliability_service=Reliability(),
    )

    with pytest.raises(ReleaseGuardValidationError):
        service.create_policy(
            policy_id="p1",
            tenant_id="tenant-a",
            minimum_reliability_score=101,
        )
