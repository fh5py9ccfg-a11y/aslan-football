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
    service.evaluate(
        evaluation_id="eval1",
        prediction_id=prediction.prediction_id,
        actual_home_goals=2,
        actual_away_goals=1,
        now=102,
    )
    return service, prediction


def test_benchmark_and_reliability():
    service, _ = build()

    benchmark = service.benchmark_models(
        benchmark_id="b1",
        club_id="c1",
        now=103,
    )
    reliability = service.reliability_report(
        report_id="r1",
        club_id="c1",
        now=104,
    )

    assert benchmark.evaluated_predictions == 1
    assert benchmark.verdict in {
        "STRONG",
        "USEFUL",
        "NEEDS_IMPROVEMENT",
    }
    assert len(reliability.buckets) == 5
    assert reliability.reliability_grade in {
        "A", "B", "C", "D",
    }


def test_audit_and_shareable_report():
    service, prediction = build()
    event = service.record_audit_event(
        event_id="a1",
        prediction_id=prediction.prediction_id,
        club_id="c1",
        event_type="CREATED",
        actor="system",
        details="Tahmin üretildi",
        now=103,
    )
    report = service.shareable_report(
        prediction_id=prediction.prediction_id,
        club_id="c1",
        data_quality_score=82,
    )

    assert event.event_type == "CREATED"
    assert report["predicted_score"]
    assert len(report["audit_events"]) == 1
    assert "kesin sonuç garantisi" in report["disclaimer"]
