import pytest

from apps.api.app.deployment_verification import (
    DeploymentVerificationError,
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


class Repository:
    def get_plan(self, plan_id):
        return type(
            "Plan",
            (),
            {"release_id": "r1"},
        )()

    def get_state(self, plan_id):
        return type(
            "State",
            (),
            {
                "status": "RUNNING",
                "rollback_reason": None,
            },
        )()


class Progressive:
    repository = Repository()


class Deployment:
    def rollback(self, **kwargs):
        raise AssertionError


def service():
    return DeploymentVerificationService(
        repository=RedisDeploymentVerificationRepository(
            Redis()
        ),
        progressive_delivery_service=Progressive(),
        deployment_manager=Deployment(),
    )


def test_required_checks_must_be_positive():
    with pytest.raises(ValueError):
        service().create_session(
            session_id="s1",
            plan_id="p1",
            deployment_slot="winner",
            required_checks=0,
        )


def test_duplicate_check_is_rejected():
    item = service()
    item.create_session(
        session_id="s1",
        plan_id="p1",
        deployment_slot="winner",
    )
    item.record_check(
        session_id="s1",
        check_id="c1",
        check_type="health",
        name="Health",
        passed=True,
        detail="ok",
    )

    with pytest.raises(
        DeploymentVerificationError
    ):
        item.record_check(
            session_id="s1",
            check_id="c1",
            check_type="health",
            name="Health",
            passed=True,
            detail="ok",
        )
