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
    return service, prediction


def test_model_registry_and_snapshot():
    service, prediction = build()
    model = service.register_model(
        model_id="model1",
        club_id="c1",
        model_version="1.0.0",
        competition="Lig",
        feature_set=("elo", "xg", "form"),
        training_sample_size=120,
        validation_brier_score=0.54,
        validation_log_loss=0.98,
        now=102,
    )
    promoted = service.promote_model(
        model_id=model.model_id,
        now=103,
    )
    snapshot = service.snapshot_prediction(
        snapshot_id="snap1",
        prediction_id=prediction.prediction_id,
        model_id=model.model_id,
        data_quality_score=82,
        now=104,
    )

    assert promoted.status == "ACTIVE"
    assert snapshot.model_id == "model1"
    assert len(
        service.repository.list_snapshots(
            prediction.prediction_id
        )
    ) == 1


def test_rolling_backtest_and_drift():
    service, prediction = build()
    service.register_model(
        model_id="model1",
        club_id="c1",
        model_version="1.0.0",
        competition="ALL",
        feature_set=("elo", "xg"),
        training_sample_size=50,
        validation_brier_score=0.6,
        validation_log_loss=1.0,
        status="ACTIVE",
        now=102,
    )
    service.evaluate(
        evaluation_id="eval1",
        prediction_id=prediction.prediction_id,
        actual_home_goals=2,
        actual_away_goals=1,
        now=103,
    )
    report = service.rolling_backtest(
        club_id="c1",
        window_size=5,
    )
    drift = service.drift_report(
        drift_id="drift1",
        club_id="c1",
        model_id="model1",
        window_size=5,
        now=104,
    )

    assert report["evaluated"] == 1
    assert drift.drift_level in {
        "LOW",
        "MEDIUM",
        "HIGH",
    }
    assert len(drift.warnings) >= 1
