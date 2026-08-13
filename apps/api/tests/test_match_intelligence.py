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
    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intelligence",
        ),
        workspace_service=workspace,
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
    return workspace, service


def test_prediction_probabilities_sum_to_100():
    _, service = build()
    service.save_opponent_profile(
        profile_id="club-profile",
        club_id="c1",
        team_name="Aslan",
        attack_rating=1.15,
        defence_rating=0.85,
        form_rating=0.75,
        home_rating=0.80,
        away_rating=0.55,
        goals_for_average=1.8,
        goals_against_average=1.0,
        sample_size=12,
        now=102,
    )
    service.save_opponent_profile(
        profile_id="opp-profile",
        club_id="c1",
        team_name="Rakip",
        attack_rating=0.95,
        defence_rating=1.10,
        form_rating=0.45,
        home_rating=0.60,
        away_rating=0.35,
        goals_for_average=1.2,
        goals_against_average=1.5,
        sample_size=10,
        now=102,
    )

    prediction = service.predict(
        prediction_id="pred1",
        club_id="c1",
        match_id="m1",
        club_profile_id="club-profile",
        opponent_profile_id="opp-profile",
        unavailable_impact=0.05,
        opponent_unavailable_impact=0.10,
        now=103,
    )

    total = (
        prediction.home_win_probability
        + prediction.draw_probability
        + prediction.away_win_probability
    )
    assert 99.9 <= total <= 100.1
    assert len(prediction.likely_scores) == 5
    assert prediction.expected_home_goals > 0


def test_prediction_evaluation_and_accuracy():
    _, service = build()
    for profile_id, name in (
        ("club", "Aslan"),
        ("opp", "Rakip"),
    ):
        service.save_opponent_profile(
            profile_id=profile_id,
            club_id="c1",
            team_name=name,
            attack_rating=1.0,
            defence_rating=1.0,
            form_rating=0.5,
            home_rating=0.5,
            away_rating=0.5,
            goals_for_average=1.3,
            goals_against_average=1.3,
            sample_size=10,
            now=102,
        )
    prediction = service.predict(
        prediction_id="pred1",
        club_id="c1",
        match_id="m1",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=103,
    )
    evaluation = service.evaluate(
        evaluation_id="eval1",
        prediction_id="pred1",
        actual_home_goals=prediction.predicted_home_goals,
        actual_away_goals=prediction.predicted_away_goals,
        now=104,
    )
    report = service.accuracy_report(
        club_id="c1"
    )

    assert evaluation.exact_score_correct is True
    assert report["result_accuracy"] == 100.0
    assert report["exact_score_accuracy"] == 100.0
