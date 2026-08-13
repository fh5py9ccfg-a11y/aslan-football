from apps.api.app.self_healing import (
    NodeHealthScorer,
    RedisSelfHealingRepository,
    SelfHealingOrchestrator,
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
    repository = RedisSelfHealingRepository(
        Redis(),
        prefix="healing",
    )
    return SelfHealingOrchestrator(
        repository=repository,
        heartbeat_timeout_seconds=10,
        quarantine_seconds=20,
        unhealthy_score=35,
        degraded_score=65,
    )


def test_health_score_degrades_under_pressure():
    healthy = NodeHealthScorer.calculate(
        cpu_percent=30,
        memory_percent=40,
        error_rate=0,
        latency_ms=50,
    )
    unhealthy = NodeHealthScorer.calculate(
        cpu_percent=98,
        memory_percent=98,
        error_rate=0.4,
        latency_ms=3000,
    )

    assert healthy >= 90
    assert unhealthy < 35
    assert healthy > unhealthy


def test_unhealthy_node_is_quarantined():
    orchestrator = build()
    orchestrator.report(
        node_id="n1",
        region="eu-west",
        role="worker",
        cpu_percent=99,
        memory_percent=99,
        error_rate=0.5,
        latency_ms=3000,
        now=100,
    )

    actions = orchestrator.reconcile(now=101)
    node = orchestrator.repository.get_node("n1")

    assert actions[0].action == "QUARANTINE"
    assert node.status == "QUARANTINED"
    assert node.quarantined_until == 121


def test_stale_heartbeat_is_quarantined():
    orchestrator = build()
    orchestrator.report(
        node_id="n1",
        region="eu-west",
        role="worker",
        cpu_percent=20,
        memory_percent=20,
        error_rate=0,
        latency_ms=20,
        now=100,
    )

    actions = orchestrator.reconcile(now=111)

    assert actions[0].reason == "Heartbeat timeout"


def test_healthy_node_rejoins_after_quarantine():
    orchestrator = build()
    orchestrator.report(
        node_id="n1",
        region="eu-west",
        role="worker",
        cpu_percent=99,
        memory_percent=99,
        error_rate=0.5,
        latency_ms=3000,
        now=100,
    )
    orchestrator.reconcile(now=101)

    orchestrator.report(
        node_id="n1",
        region="eu-west",
        role="worker",
        cpu_percent=20,
        memory_percent=20,
        error_rate=0,
        latency_ms=20,
        now=120,
    )
    actions = orchestrator.reconcile(now=121)
    node = orchestrator.repository.get_node("n1")

    assert actions[0].action == "REJOIN"
    assert node.status == "HEALTHY"
