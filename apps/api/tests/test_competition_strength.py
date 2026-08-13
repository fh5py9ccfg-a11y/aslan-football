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


def test_competition_strength_from_results():
    redis = Redis()
    workspace = MVPWorkspaceService(
        repository=RedisMVPRepository(
            redis,
            prefix="mvp",
        )
    )
    workspace.create_club(
        club_id="c1",
        name="Aslan",
        country="TR",
        now=100,
    )
    for index, score in enumerate(
        ((3, 2), (1, 1), (2, 0)),
        start=1,
    ):
        workspace.create_match(
            match_id=f"m{index}",
            club_id="c1",
            opponent=f"Rakip {index}",
            competition="Lig",
            kickoff_at=100 + index,
            venue="HOME",
            now=100,
        )
        workspace.complete_match(
            match_id=f"m{index}",
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
    report = service.competition_strength(
        club_id="c1",
        competition="Lig",
    )

    assert report["sample_size"] == 3
    assert 0.7 <= report["goal_environment"] <= 1.35
