from apps.api.app.progressive_delivery import (
    ProgressiveDeliveryService,
    RedisProgressiveDeliveryRepository,
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


class Reliability:
    def __init__(
        self,
        score=100,
        warning=0,
        critical=0,
    ):
        self.score = score
        self.warning = warning
        self.critical = critical

    def reliability_score(self, **kwargs):
        return {
            "score": self.score,
            "status": "HEALTHY",
            "warning_slos": self.warning,
            "critical_slos": self.critical,
        }


class GuardDecision:
    allowed = True
    reliability_score = 100
    warning_slos = 0
    critical_slos = 0
    reason = "ok"


class Guard:
    def evaluate(self, **kwargs):
        return GuardDecision()


def build(reliability=None):
    return ProgressiveDeliveryService(
        repository=(
            RedisProgressiveDeliveryRepository(
                Redis(),
                prefix="delivery",
            )
        ),
        reliability_service=(
            reliability or Reliability()
        ),
        release_guard_service=Guard(),
    )


def test_progressive_delivery_promotes_and_completes():
    service = build()
    service.create_plan(
        plan_id="p1",
        tenant_id="tenant-a",
        release_id="r1",
        stages=(10, 50, 100),
        now=100,
    )
    started = service.start(
        plan_id="p1",
        gate_decision_id="g1",
        now=101,
    )

    first_state, first_eval = service.evaluate(
        plan_id="p1",
        evaluation_id="e1",
        now=102,
    )
    second_state, second_eval = service.evaluate(
        plan_id="p1",
        evaluation_id="e2",
        now=103,
    )
    final_state, final_eval = service.evaluate(
        plan_id="p1",
        evaluation_id="e3",
        now=104,
    )

    assert started.current_percentage == 10
    assert first_eval.action == "PROMOTE"
    assert first_state.current_percentage == 50
    assert second_state.current_percentage == 100
    assert second_eval.action == "PROMOTE"
    assert final_eval.action == "COMPLETE"
    assert final_state.status == "COMPLETED"


def test_quality_violation_triggers_rollback():
    service = build(
        Reliability(
            score=20,
            warning=1,
            critical=1,
        )
    )
    service.create_plan(
        plan_id="p1",
        tenant_id="tenant-a",
        release_id="r1",
        stages=(10, 100),
        minimum_reliability_score=70,
        max_warning_slos=0,
        max_critical_slos=0,
        auto_rollback=True,
        now=100,
    )
    service.start(
        plan_id="p1",
        gate_decision_id="g1",
        now=101,
    )

    state, evaluation = service.evaluate(
        plan_id="p1",
        evaluation_id="e1",
        now=102,
    )

    assert evaluation.action == "ROLLBACK"
    assert state.status == "ROLLED_BACK"
    assert state.rollback_reason is not None


def test_quality_violation_can_pause():
    service = build(
        Reliability(
            score=60,
            warning=1,
        )
    )
    service.create_plan(
        plan_id="p1",
        tenant_id="tenant-a",
        release_id="r1",
        stages=(10, 100),
        auto_rollback=False,
        now=100,
    )
    service.start(
        plan_id="p1",
        gate_decision_id="g1",
        now=101,
    )

    state, evaluation = service.evaluate(
        plan_id="p1",
        evaluation_id="e1",
        now=102,
    )
    resumed = service.resume(
        plan_id="p1",
        now=103,
    )

    assert evaluation.action == "PAUSE"
    assert state.status == "PAUSED"
    assert resumed.status == "RUNNING"
