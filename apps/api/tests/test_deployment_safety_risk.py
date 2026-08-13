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
    def reliability_score(self, **kwargs):
        return {
            "score": 40,
            "status": "AT_RISK",
            "warning_slos": 1,
            "critical_slos": 1,
        }


@dataclass
class Rollout:
    status: str = "PAUSED"


@dataclass
class Verification:
    status: str = "FAILED"


class Progressive:
    class repository:
        @staticmethod
        def get_state(plan_id):
            return Rollout()


class VerificationService:
    class repository:
        @staticmethod
        def get_session(session_id):
            return Verification()


def test_high_risk_snapshot():
    service = DeploymentSafetyService(
        repository=RedisDeploymentSafetyRepository(
            Redis()
        ),
        reliability_service=Reliability(),
        progressive_delivery_service=Progressive(),
        deployment_verification_service=(
            VerificationService()
        ),
    )

    risk = service.calculate_risk(
        tenant_id="t",
        release_id="r",
        plan_id="p",
        verification_session_id="v",
        changed_files=120,
        affected_services=8,
        now=100,
    )

    assert risk.risk_level == "CRITICAL"
    assert risk.risk_score >= 75
    assert len(risk.reasons) >= 5
