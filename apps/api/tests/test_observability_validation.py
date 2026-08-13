import pytest

from apps.api.app.pilot_observability import (
    ObservabilityValidationError,
    PilotObservabilityService,
    RedisPilotObservabilityRepository,
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


class Intelligence:
    repository = object()


def test_invalid_category_rejected():
    service = PilotObservabilityService(
        repository=RedisPilotObservabilityRepository(
            Redis(),
            prefix="obs",
        ),
        intelligence_service=Intelligence(),
    )

    with pytest.raises(ObservabilityValidationError):
        service.record_event(
            event_id="e1",
            club_id="c1",
            category="UNKNOWN",
            severity="INFO",
            component="api",
            message="x",
            now=100,
        )
