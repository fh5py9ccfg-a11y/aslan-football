from apps.api.app.match_intelligence import (
    MatchIntelligenceService,
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


def test_elo_is_derived_from_match_results():
    redis = Redis()
    workspace = MVPWorkspaceService(
        repository=RedisMVPRepository(redis, prefix="mvp")
    )
    workspace.create_club(
        club_id="c1",
        name="Aslan",
        country="TR",
        now=100,
    )
    for i, score in enumerate(((2, 0), (1, 0), (3, 1)), start=1):
        workspace.create_match(
            match_id=f"m{i}",
            club_id="c1",
            opponent=f"Rakip {i}",
            competition="Lig",
            kickoff_at=100 + i,
            venue="HOME",
            now=100,
        )
        workspace.complete_match(
            match_id=f"m{i}",
            club_id="c1",
            goals_for=score[0],
            goals_against=score[1],
        )

    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )
    profile = service.derive_club_profile(
        profile_id="club",
        club_id="c1",
        now=200,
    )

    assert profile.elo_rating > 1500
    assert profile.xg_for_average > 0
