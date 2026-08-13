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


def test_invalid_league_strength_rejected():
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
        service.match_context_report(
            context_id="ctx1",
            club_id="c1",
            match_id="m1",
            league_strength=2.0,
            rest_days=5,
            opponent_rest_days=5,
            travel_km=0,
            temperature_c=20,
            wind_kmh=0,
            precipitation_mm=0,
            referee_card_rate=4,
            now=100,
        )
