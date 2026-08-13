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
        repository=RedisMVPRepository(redis, prefix="mvp")
    )
    workspace.create_club(
        club_id="c1",
        name="Aslan",
        country="TR",
        now=100,
    )
    workspace.create_match(
        match_id="m1",
        club_id="c1",
        opponent="Rakip",
        competition="Lig",
        kickoff_at=300,
        venue="HOME",
        now=101,
    )
    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )
    service.save_opponent_profile(
        profile_id="club",
        club_id="c1",
        team_name="Aslan",
        attack_rating=1.1,
        defence_rating=0.9,
        form_rating=0.7,
        home_rating=0.8,
        away_rating=0.5,
        goals_for_average=1.7,
        goals_against_average=1.0,
        sample_size=12,
        elo_rating=1580,
        xg_for_average=1.65,
        xg_against_average=0.95,
        now=102,
    )
    service.save_opponent_profile(
        profile_id="opp",
        club_id="c1",
        team_name="Rakip",
        attack_rating=0.95,
        defence_rating=1.05,
        form_rating=0.45,
        home_rating=0.6,
        away_rating=0.35,
        goals_for_average=1.2,
        goals_against_average=1.4,
        sample_size=10,
        elo_rating=1490,
        xg_for_average=1.1,
        xg_against_average=1.35,
        now=102,
    )
    return service


def test_scenarios_are_created():
    service = build()
    prediction = service.predict(
        prediction_id="pred1",
        club_id="c1",
        match_id="m1",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=103,
    )

    scenarios = service.create_scenarios(
        prediction_id=prediction.prediction_id,
        now=104,
    )

    assert len(scenarios) == 3
    assert scenarios[0].label == "FULL_SQUAD"
    assert scenarios[1].expected_home_goals < scenarios[0].expected_home_goals


def test_calibration_uses_evaluated_predictions():
    service = build()
    prediction = service.predict(
        prediction_id="pred1",
        club_id="c1",
        match_id="m1",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=103,
    )
    service.evaluate(
        evaluation_id="eval1",
        prediction_id="pred1",
        actual_home_goals=2,
        actual_away_goals=1,
        now=104,
    )

    calibration = service.calibrate(
        calibration_id="cal1",
        club_id="c1",
        now=105,
    )

    assert calibration.sample_size == 1
    assert calibration.brier_score >= 0
    assert calibration.log_loss >= 0
