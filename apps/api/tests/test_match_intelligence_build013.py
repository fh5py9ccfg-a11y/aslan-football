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


def build():
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
    for index, opponent in enumerate(
        ("Rakip", "Rakip", "Başka Rakip"),
        start=1,
    ):
        workspace.create_match(
            match_id=f"m{index}",
            club_id="c1",
            opponent=opponent,
            competition="Lig",
            kickoff_at=100 + index,
            venue="HOME" if index < 3 else "AWAY",
            now=100,
        )
    workspace.complete_match(
        match_id="m1",
        club_id="c1",
        goals_for=2,
        goals_against=1,
    )
    workspace.complete_match(
        match_id="m2",
        club_id="c1",
        goals_for=1,
        goals_against=1,
    )

    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )
    for profile_id, name, elo in (
        ("club", "Aslan", 1580),
        ("opp", "Rakip", 1500),
    ):
        service.save_opponent_profile(
            profile_id=profile_id,
            club_id="c1",
            team_name=name,
            attack_rating=1.05,
            defence_rating=0.98,
            form_rating=0.60,
            home_rating=0.65,
            away_rating=0.45,
            goals_for_average=1.45,
            goals_against_average=1.15,
            sample_size=12,
            elo_rating=elo,
            xg_for_average=1.4,
            xg_against_average=1.1,
            now=100,
        )
    prediction = service.predict(
        prediction_id="pred1",
        club_id="c1",
        match_id="m3",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=101,
    )
    return service, prediction


def test_post_match_learning_and_memory():
    service, prediction = build()
    learning = service.post_match_learning(
        learning_id="l1",
        prediction_id=prediction.prediction_id,
        club_id="c1",
        actual_home_goals=0,
        actual_away_goals=2,
        now=102,
    )
    memories = service.rebuild_opponent_memory(
        club_id="c1",
        now=103,
    )

    assert learning.result_error in {True, False}
    assert len(learning.root_causes) >= 1
    assert len(memories) == 1
    assert memories[0].opponent_name == "Rakip"


def test_similar_matches_and_recalibration_advisor():
    service, prediction = build()
    service.evaluate(
        evaluation_id="e1",
        prediction_id=prediction.prediction_id,
        actual_home_goals=0,
        actual_away_goals=2,
        now=102,
    )
    similar = service.similar_matches(
        club_id="c1",
        match_id="m3",
        limit=5,
    )
    recommendation = service.recalibration_recommendation(
        club_id="c1"
    )

    assert len(similar) == 2
    assert "recommended" in recommendation
    assert len(recommendation["reasons"]) >= 1
