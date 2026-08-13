from apps.api.app.reliability_management import (
    RedisReliabilityRepository,
    ReliabilityManagementService,
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
    return ReliabilityManagementService(
        repository=RedisReliabilityRepository(
            Redis(),
            prefix="reliability",
        )
    )


def test_error_budget_is_healthy_below_burn_threshold():
    service = build()
    service.create_slo(
        slo_id="availability",
        tenant_id="tenant-a",
        service="api",
        indicator="successful_requests",
        target=0.99,
        window_seconds=3600,
        now=100,
    )
    service.record(
        observation_id="o1",
        slo_id="availability",
        good_events=995,
        total_events=1000,
        observed_at=110,
    )

    snapshot = service.calculate(
        slo_id="availability",
        now=120,
    )

    assert snapshot.achieved == 0.995
    assert snapshot.burn_rate == 0.5
    assert snapshot.status == "HEALTHY"


def test_error_budget_becomes_critical():
    service = build()
    service.create_slo(
        slo_id="availability",
        tenant_id="tenant-a",
        service="api",
        indicator="successful_requests",
        target=0.99,
        window_seconds=3600,
        now=100,
    )
    service.record(
        observation_id="o1",
        slo_id="availability",
        good_events=970,
        total_events=1000,
        observed_at=110,
    )

    snapshot = service.calculate(
        slo_id="availability",
        now=120,
    )

    assert snapshot.burn_rate == 3.0
    assert snapshot.status == "CRITICAL"
    assert snapshot.remaining_percent == 0.0


def test_tenant_reliability_score_combines_slos():
    service = build()
    service.create_slo(
        slo_id="api",
        tenant_id="tenant-a",
        service="api",
        indicator="availability",
        target=0.99,
        window_seconds=3600,
        now=100,
    )
    service.create_slo(
        slo_id="worker",
        tenant_id="tenant-a",
        service="worker",
        indicator="success_rate",
        target=0.95,
        window_seconds=3600,
        now=100,
    )
    service.record(
        observation_id="api-o1",
        slo_id="api",
        good_events=995,
        total_events=1000,
        observed_at=110,
    )
    service.record(
        observation_id="worker-o1",
        slo_id="worker",
        good_events=950,
        total_events=1000,
        observed_at=110,
    )

    score = service.reliability_score(
        tenant_id="tenant-a",
        now=120,
    )

    assert score["slo_count"] == 2
    assert 0 <= score["score"] <= 100
