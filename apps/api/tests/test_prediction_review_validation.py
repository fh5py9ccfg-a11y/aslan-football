import pytest

from apps.api.app.match_intelligence import (
    MatchIntelligenceService,
    MatchIntelligenceValidationError,
    RedisMatchIntelligenceRepository,
)
from apps.api.app.mvp_workspace import (
    MVPWorkspaceService,
    RedisMVPRepository,
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


def test_invalid_review_status_rejected():
    redis = Redis()
    workspace = MVPWorkspaceService(
        repository=RedisMVPRepository(redis, prefix="mvp")
    )
    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )

    with pytest.raises(MatchIntelligenceValidationError):
        service.review_prediction(
            decision_id="d1",
            prediction_id="missing",
            club_id="c1",
            status="UNKNOWN",
            reviewer="coach",
            now=100,
        )
