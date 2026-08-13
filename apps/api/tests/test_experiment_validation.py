import pytest

from apps.api.app.pilot_experiments import (
    ExperimentValidationError,
    PilotExperimentService,
    RedisPilotExperimentRepository,
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


def test_invalid_rollout_rejected():
    service = PilotExperimentService(
        repository=RedisPilotExperimentRepository(
            Redis(),
            prefix="exp",
        )
    )

    with pytest.raises(ExperimentValidationError):
        service.create_flag(
            flag_id="f1",
            club_id="c1",
            name="x",
            enabled=True,
            rollout_percentage=101,
            now=100,
        )
