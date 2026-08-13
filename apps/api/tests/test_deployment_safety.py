from dataclasses import dataclass

from apps.api.app.deployment_safety import (
    DeploymentSafetyService,
    RedisDeploymentSafetyRepository,
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
    def __init__(self, score=90, warning=0, critical=0):
        self.result = {
            "score": score,
            "status": "HEALTHY",
            "warning_slos": warning,
            "critical_slos": critical,
        }

    def reliability_score(self, **kwargs):
        return self.result


@dataclass
class Rollout:
    status: str = "COMPLETED"


@dataclass
class Verification:
    status: str = "VERIFIED"


class ProgressiveRepository:
    def get_state(self, plan_id):
        return Rollout()


class VerificationRepository:
    def get_session(self, session_id):
        return Verification()


class Progressive:
    repository = ProgressiveRepository()


class VerificationService:
    repository = VerificationRepository()


def build(reliability=None):
    return DeploymentSafetyService(
        repository=RedisDeploymentSafetyRepository(
            Redis(),
            prefix="safety",
        ),
        reliability_service=(
            reliability or Reliability()
        ),
        progressive_delivery_service=Progressive(),
        deployment_verification_service=(
            VerificationService()
        ),
    )


def test_low_risk_approved_release_is_allowed():
    service = build()
    service.calculate_risk(
        tenant_id="t",
        release_id="r",
        plan_id="p",
        verification_session_id="v",
        changed_files=5,
        affected_services=1,
        now=100,
    )
    service.approve(
        approval_id="a1",
        tenant_id="t",
        release_id="r",
        role="ops",
        actor="ops-user",
        decision="APPROVED",
        comment="Looks good",
        now=101,
    )
    service.approve(
        approval_id="a2",
        tenant_id="t",
        release_id="r",
        role="mlops",
        actor="ml-user",
        decision="APPROVED",
        comment="Model checks passed",
        now=102,
    )

    decision = service.evaluate(
        decision_id="d1",
        tenant_id="t",
        release_id="r",
        now=103,
    )

    assert decision.allowed is True
    assert decision.status == "ALLOWED"
    assert decision.risk_score < 25


def test_active_freeze_blocks_release():
    service = build()
    service.calculate_risk(
        tenant_id="t",
        release_id="r",
        plan_id="p",
        verification_session_id="v",
        changed_files=1,
        affected_services=1,
        now=100,
    )
    service.approve(
        approval_id="a1",
        tenant_id="t",
        release_id="r",
        role="ops",
        actor="ops-user",
        decision="APPROVED",
        comment="approved",
        now=101,
    )
    service.approve(
        approval_id="a2",
        tenant_id="t",
        release_id="r",
        role="mlops",
        actor="ml-user",
        decision="APPROVED",
        comment="approved",
        now=102,
    )
    service.create_freeze(
        freeze_id="f1",
        tenant_id="t",
        starts_at=90,
        ends_at=200,
        reason="Quarter close freeze",
        emergency_bypass_allowed=False,
        created_by="ops-user",
        now=80,
    )

    decision = service.evaluate(
        decision_id="d1",
        tenant_id="t",
        release_id="r",
        now=110,
    )

    assert decision.allowed is False
    assert decision.status == "BLOCKED"
    assert decision.freeze_id == "f1"


def test_emergency_can_bypass_allowed_freeze():
    service = build()
    service.calculate_risk(
        tenant_id="t",
        release_id="r",
        plan_id="p",
        verification_session_id="v",
        changed_files=1,
        affected_services=1,
        now=100,
    )
    service.approve(
        approval_id="a1",
        tenant_id="t",
        release_id="r",
        role="ops",
        actor="ops-user",
        decision="APPROVED",
        comment="approved",
        now=101,
    )
    service.approve(
        approval_id="a2",
        tenant_id="t",
        release_id="r",
        role="mlops",
        actor="ml-user",
        decision="APPROVED",
        comment="approved",
        now=102,
    )
    service.create_freeze(
        freeze_id="f1",
        tenant_id="t",
        starts_at=90,
        ends_at=200,
        reason="Regular freeze",
        emergency_bypass_allowed=True,
        created_by="ops-user",
        now=80,
    )

    decision = service.evaluate(
        decision_id="d1",
        tenant_id="t",
        release_id="r",
        emergency=True,
        now=110,
    )

    assert decision.allowed is True
    assert decision.status == "ALLOWED"
