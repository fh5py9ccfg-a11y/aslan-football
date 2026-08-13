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
    workspace.create_player(
        player_id="p1",
        club_id="c1",
        name="Forvet",
        position="ST",
        age=24,
        market_value=4,
        now=100,
    )
    workspace.create_player(
        player_id="p2",
        club_id="c1",
        name="Orta saha",
        position="CM",
        age=23,
        market_value=3,
        now=100,
    )
    workspace.set_player_availability(
        club_id="c1",
        player_id="p1",
        availability="INJURED",
        note="Hamstring",
    )
    workspace.create_match(
        match_id="m1",
        club_id="c1",
        opponent="Rakip",
        competition="Lig",
        kickoff_at=300,
        venue="HOME",
        now=100,
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
        attack_rating=1.15,
        defence_rating=0.90,
        form_rating=0.70,
        home_rating=0.80,
        away_rating=0.50,
        goals_for_average=1.7,
        goals_against_average=1.0,
        sample_size=12,
        elo_rating=1580,
        xg_for_average=1.6,
        xg_against_average=1.0,
        now=100,
    )
    service.save_opponent_profile(
        profile_id="opp",
        club_id="c1",
        team_name="Rakip",
        attack_rating=0.95,
        defence_rating=1.05,
        form_rating=0.45,
        home_rating=0.60,
        away_rating=0.35,
        goals_for_average=1.2,
        goals_against_average=1.4,
        sample_size=10,
        elo_rating=1490,
        xg_for_average=1.1,
        xg_against_average=1.35,
        now=100,
    )
    return workspace, service


def test_automatic_unavailable_impact():
    _, service = build()

    impact = service.automatic_unavailable_impact(
        club_id="c1"
    )

    assert impact > 0
    assert impact <= 0.50


def test_data_quality_and_ensemble():
    _, service = build()
    prediction = service.predict(
        prediction_id="pred1",
        club_id="c1",
        match_id="m1",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=101,
    )
    quality = service.data_quality_report(
        report_id="q1",
        club_id="c1",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=101,
    )
    ensemble = service.create_ensemble(
        ensemble_id="ens1",
        prediction_id=prediction.prediction_id,
        data_quality_report_id=quality.report_id,
        now=102,
    )

    total = (
        ensemble.blended_home_probability
        + ensemble.blended_draw_probability
        + ensemble.blended_away_probability
    )
    assert quality.grade in {"A", "B", "C", "D"}
    assert 99.9 <= total <= 100.1
    assert ensemble.home_probability_interval[0] <= (
        ensemble.blended_home_probability
    )
    assert ensemble.home_probability_interval[1] >= (
        ensemble.blended_home_probability
    )
