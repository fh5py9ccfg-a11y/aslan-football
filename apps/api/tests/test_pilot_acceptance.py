from apps.api.app.final_pilot import FinalPilotService
from apps.api.app.match_intelligence import (
    MatchIntelligenceService,
    RedisMatchIntelligenceRepository,
)
from apps.api.app.mvp_workspace import (
    MVPWorkspaceService,
    RedisMVPRepository,
)
from apps.api.app.pilot_acceptance import (
    PilotAcceptanceService,
)
from apps.api.app.pilot_observability import (
    PilotObservabilityService,
    RedisPilotObservabilityRepository,
)
from apps.api.app.pilot_stabilization import (
    PilotStabilizationService,
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
        repository=RedisMVPRepository(redis, prefix="mvp")
    )
    intelligence = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )
    observability = PilotObservabilityService(
        repository=RedisPilotObservabilityRepository(
            redis,
            prefix="obs",
        ),
        intelligence_service=intelligence,
    )
    stabilization = PilotStabilizationService(
        workspace_service=workspace,
        intelligence_service=intelligence,
    )
    final = FinalPilotService(
        workspace_service=workspace,
        intelligence_service=intelligence,
        observability_service=observability,
    )
    return PilotAcceptanceService(
        final_pilot_service=final,
        stabilization_service=stabilization,
        observability_service=observability,
        intelligence_service=intelligence,
    )


def test_repeatability_is_stable():
    service = build()
    result = service.repeatability_check(
        club_id="demo",
        now=100,
    )

    assert result["stable"] is True
    assert result["first"]["players"] == 18
    assert result["second"]["matches"] == 3


def test_acceptance_report_has_fingerprint(monkeypatch):
    monkeypatch.setenv(
        "MVP_AUTH_SECRET",
        "a-very-strong-production-auth-key-1234567890",
    )
    monkeypatch.setenv(
        "MVP_AUTH_TTL_SECONDS",
        "86400",
    )
    monkeypatch.setenv(
        "MVP_AUTH_PREFIX",
        "aslan:mvp-auth",
    )
    service = build()
    report = service.run_acceptance(
        report_id="a1",
        club_id="demo",
        reviewer="coach",
        now=100,
    )

    assert report.status in {
        "ACCEPTED",
        "CONDITIONAL",
        "REJECTED",
    }
    assert len(report.fingerprint) == 64
    assert len(report.checks) == 9
