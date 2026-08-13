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
        now=100,
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
        match_id="m1",
        club_profile_id="club",
        opponent_profile_id="opp",
        now=101,
    )
    return service, prediction


def test_match_context_and_live_update():
    service, prediction = build()
    context = service.match_context_report(
        context_id="ctx1",
        club_id="c1",
        match_id="m1",
        league_strength=1.0,
        rest_days=3,
        opponent_rest_days=6,
        travel_km=900,
        temperature_c=29,
        wind_kmh=15,
        precipitation_mm=0,
        referee_card_rate=5.0,
        now=102,
    )
    live = service.live_update(
        state_id="live1",
        prediction_id=prediction.prediction_id,
        minute=60,
        home_goals=1,
        away_goals=0,
        home_red_cards=0,
        away_red_cards=0,
        home_xg_live=1.4,
        away_xg_live=0.5,
        now=103,
    )

    total = (
        live.home_win_probability
        + live.draw_probability
        + live.away_win_probability
    )
    assert context.fatigue_modifier > 0
    assert 99.9 <= total <= 100.1
    assert live.home_win_probability > live.away_win_probability


def test_explainability_report():
    service, prediction = build()
    context = service.match_context_report(
        context_id="ctx1",
        club_id="c1",
        match_id="m1",
        league_strength=1.0,
        rest_days=5,
        opponent_rest_days=5,
        travel_km=100,
        temperature_c=20,
        wind_kmh=10,
        precipitation_mm=0,
        referee_card_rate=4.0,
        now=102,
    )
    report = service.explain_prediction(
        report_id="exp1",
        prediction_id=prediction.prediction_id,
        context_id=context.context_id,
        now=103,
    )

    assert len(report.contributions) >= 4
    assert report.strongest_positive_factor
    assert "Beklenen gol dengesi" in report.narrative
