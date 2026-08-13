from apps.api.app.pilot_experiments import (
    PilotExperimentService,
    RedisPilotExperimentRepository,
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
    return PilotExperimentService(
        repository=RedisPilotExperimentRepository(
            Redis(),
            prefix="exp",
        )
    )


def test_feature_flag_is_deterministic():
    service = build()
    service.create_flag(
        flag_id="flag1",
        club_id="c1",
        name="Yeni tahmin ekranı",
        enabled=True,
        rollout_percentage=50,
        allowed_roles=("ANALYST",),
        variant="v2",
        now=100,
    )

    first = service.evaluate_flag(
        flag_id="flag1",
        user_id="u1",
        role="ANALYST",
    )
    second = service.evaluate_flag(
        flag_id="flag1",
        user_id="u1",
        role="ANALYST",
    )

    assert first == second
    assert first["role_allowed"] is True


def test_experiment_report_and_rollback():
    service = build()
    service.create_flag(
        flag_id="flag1",
        club_id="c1",
        name="Yeni tahmin ekranı",
        enabled=True,
        rollout_percentage=100,
        variant="v2",
        now=100,
    )
    experiment = service.create_experiment(
        experiment_id="exp1",
        club_id="c1",
        name="Tahmin ekranı testi",
        feature="MATCH_INTELLIGENCE",
        control_variant="v1",
        treatment_variant="v2",
        rollout_percentage=100,
        primary_metric="rating",
        status="RUNNING",
        now=100,
    )
    for index in range(10):
        variant = "v1" if index < 5 else "v2"
        service.record_metric(
            metric_id=f"m{index}",
            experiment_id=experiment.experiment_id,
            club_id="c1",
            user_id=f"u{index}",
            variant=variant,
            metric_name="rating",
            metric_value=3 if variant == "v1" else 4,
            success=True,
            now=101 + index,
        )

    report = service.report(
        report_id="r1",
        experiment_id="exp1",
        now=200,
    )
    rolled_back = service.rollback_experiment(
        experiment_id="exp1",
        flag_id="flag1",
        now=201,
    )

    assert report.winner == "v2"
    assert report.uplift_percentage > 0
    assert rolled_back["experiment"]["status"] == "ROLLED_BACK"
    assert rolled_back["flag"]["enabled"] is False
