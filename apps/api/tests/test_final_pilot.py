from apps.api.app.final_pilot import FinalPilotService
from apps.api.app.match_intelligence import (
    MatchIntelligenceService,
    RedisMatchIntelligenceRepository,
)
from apps.api.app.mvp_workspace import (
    MVPWorkspaceService,
    RedisMVPRepository,
)
from apps.api.app.pilot_observability import (
    PilotObservabilityService,
    RedisPilotObservabilityRepository,
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


def test_final_pilot_is_ready_after_seed():
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
    service = FinalPilotService(
        workspace_service=workspace,
        intelligence_service=intelligence,
        observability_service=observability,
    )

    report = service.run_final_pilot(
        report_id="final1",
        club_id="demo-club",
        reviewer="coach",
        now=100,
    )

    assert report.demo_seeded is True
    assert report.players_ready is True
    assert report.fixtures_ready is True
    assert report.profiles_ready is True
    assert report.prediction_ready is True
    assert report.final_status == "READY"
