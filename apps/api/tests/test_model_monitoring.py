from apps.api.app.model_monitoring import (
    DriftDetector,
    ModelMonitoringService,
    RedisModelMonitoringRepository,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


def service():
    return ModelMonitoringService(
        repository=RedisModelMonitoringRepository(
            Redis(),
            prefix="monitoring",
        )
    )


def test_model_health_snapshot():
    monitor = service()

    snapshot = monitor.update_health(
        model_id="m1",
        probabilities=(0.9, 0.1, 0.8, 0.2),
        outcomes=(1, 0, 1, 0),
        now=100,
    )

    assert snapshot.samples == 4
    assert snapshot.accuracy == 1.0
    assert snapshot.health_score >= 80
    assert snapshot.status == "HEALTHY"


def test_prediction_drift_creates_review_for_high_signal():
    monitor = service()
    baseline = tuple([0.1] * 50 + [0.2] * 50)
    current = tuple([0.8] * 50 + [0.9] * 50)

    signal = monitor.detect_prediction_drift(
        model_id="m1",
        baseline=baseline,
        current=current,
        now=100,
    )

    assert signal.severity in {"HIGH", "CRITICAL"}
    reviews = monitor.repository.list_reviews(
        status="OPEN"
    )
    assert len(reviews) == 1


def test_feature_drift_mean_shift():
    score = DriftDetector.mean_shift(
        baseline=(1.0, 1.1, 0.9, 1.0),
        current=(3.0, 3.1, 2.9, 3.0),
    )

    assert score > 3


def test_shadow_compare():
    monitor = service()

    result = monitor.shadow_compare(
        champion_probabilities=(0.7, 0.2),
        shadow_probabilities=(0.8, 0.4),
    )

    assert result["samples"] == 2
    assert result["mean_absolute_difference"] == 0.15
