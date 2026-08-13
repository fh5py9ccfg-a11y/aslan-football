from dataclasses import dataclass

from apps.api.app.deployment_verification import (
    DeploymentVerificationService,
    RedisDeploymentVerificationRepository,
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


@dataclass
class Plan:
    release_id: str = "release-1"


@dataclass
class State:
    status: str = "COMPLETED"
    rollback_reason: str | None = None


class ProgressiveRepository:
    def __init__(self):
        self.plan = Plan()
        self.state = State()

    def get_plan(self, plan_id):
        return self.plan

    def get_state(self, plan_id):
        return self.state


class Progressive:
    def __init__(self):
        self.repository = ProgressiveRepository()


@dataclass
class Deployment:
    generation: int = 4
    champion_model_id: str = "model-v1"


class DeploymentManager:
    def __init__(self):
        self.calls = 0

    def rollback(self, *, slot, now=None):
        self.calls += 1
        return Deployment()


def build():
    manager = DeploymentManager()
    service = DeploymentVerificationService(
        repository=RedisDeploymentVerificationRepository(
            Redis(),
            prefix="verify",
        ),
        progressive_delivery_service=Progressive(),
        deployment_manager=manager,
    )
    return service, manager


def test_successful_checks_finalize_session():
    service, _ = build()
    service.create_session(
        session_id="s1",
        plan_id="p1",
        deployment_slot="winner",
        required_checks=2,
        now=100,
    )
    state, _ = service.record_check(
        session_id="s1",
        check_id="c1",
        check_type="health",
        name="API health",
        passed=True,
        detail="ok",
        observed_at=101,
    )
    state, _ = service.record_check(
        session_id="s1",
        check_id="c2",
        check_type="smoke",
        name="Prediction smoke",
        passed=True,
        detail="ok",
        observed_at=102,
    )
    finalized = service.finalize(
        session_id="s1",
        now=103,
    )

    assert state.status == "VERIFIED"
    assert finalized.status == "VERIFIED"
    assert finalized.passed_checks == 2


def test_failed_check_allows_rollback():
    service, manager = build()
    service.create_session(
        session_id="s1",
        plan_id="p1",
        deployment_slot="winner",
        now=100,
    )
    failed, _ = service.record_check(
        session_id="s1",
        check_id="c1",
        check_type="metric",
        name="Error rate",
        passed=False,
        detail="Error rate threshold exceeded",
        value=0.12,
        threshold=0.05,
        observed_at=101,
    )
    rolled_back = service.execute_rollback(
        session_id="s1",
        now=102,
    )

    assert failed.status == "FAILED"
    assert rolled_back.status == "ROLLED_BACK"
    assert rolled_back.rollback_executed is True
    assert rolled_back.rollback_model_id == "model-v1"
    assert manager.calls == 1


def test_rollback_is_idempotent():
    service, manager = build()
    service.create_session(
        session_id="s1",
        plan_id="p1",
        deployment_slot="winner",
        now=100,
    )
    service.record_check(
        session_id="s1",
        check_id="c1",
        check_type="health",
        name="Health",
        passed=False,
        detail="failed",
        observed_at=101,
    )
    first = service.execute_rollback(
        session_id="s1",
        now=102,
    )
    second = service.execute_rollback(
        session_id="s1",
        now=103,
    )

    assert first == second
    assert manager.calls == 1
