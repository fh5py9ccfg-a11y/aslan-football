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
    for i in range(1, 4):
        workspace.create_match(
            match_id=f"m{i}",
            club_id="c1",
            opponent=f"Rakip {i}",
            competition="Lig",
            kickoff_at=100 + i,
            venue="HOME" if i % 2 else "AWAY",
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
    return service


def test_batch_prediction_creates_upcoming_predictions():
    service = build()

    items = service.batch_predict_upcoming(
        club_id="c1",
        club_profile_id="club",
        opponent_profile_id="opp",
        limit=2,
        now=101,
    )

    assert len(items) == 2
    assert items[0].prediction_id.startswith("batch:")


def test_alert_review_and_decision_report():
    service = build()
    prediction = service.batch_predict_upcoming(
        club_id="c1",
        club_profile_id="club",
        opponent_profile_id="opp",
        limit=1,
        now=101,
    )[0]
    alerts = service.generate_alerts(
        club_id="c1",
        prediction_id=prediction.prediction_id,
        data_quality_score=80,
        now=102,
    )
    decision = service.review_prediction(
        decision_id="d1",
        prediction_id=prediction.prediction_id,
        club_id="c1",
        status="APPROVED",
        reviewer="coach",
        note="Kadro kontrol edildi",
        now=103,
    )
    report = service.decision_report(
        report_id="r1",
        prediction_id=prediction.prediction_id,
        club_id="c1",
        data_quality_score=80,
        now=104,
    )

    assert len(alerts) >= 1
    assert decision.status == "APPROVED"
    assert report.approval_status == "APPROVED"
    assert len(report.tactical_focus) >= 1
