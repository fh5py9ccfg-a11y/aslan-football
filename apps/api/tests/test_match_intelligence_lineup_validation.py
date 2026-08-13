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


def test_lineup_requires_seven_players():
    redis = Redis()
    workspace = MVPWorkspaceService(
        repository=RedisMVPRepository(redis, prefix="mvp")
    )
    workspace.create_club(
        club_id="c1",
        name="Club",
        country="TR",
        now=100,
    )
    for index in range(1, 7):
        workspace.create_player(
            player_id=f"p{index}",
            club_id="c1",
            name=f"Player {index}",
            position="CM",
            age=22,
            market_value=2,
            now=100,
        )
    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )

    with pytest.raises(MatchIntelligenceValidationError):
        service.lineup_impact_report(
            report_id="r1",
            club_id="c1",
            match_id="m1",
            selected_player_ids=tuple(
                f"p{i}" for i in range(1, 7)
            ),
            now=101,
        )
