from apps.api.app.match_intelligence import (
    MatchIntelligenceService,
    RedisMatchIntelligenceRepository,
)
from apps.api.app.mvp_workspace import (
    MVPWorkspaceService,
    RedisMVPRepository,
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


def test_release_gate_blocks_empty_club():
    redis = Redis()
    workspace = MVPWorkspaceService(
        repository=RedisMVPRepository(redis, prefix="mvp")
    )
    workspace.create_club(
        club_id="c1",
        name="Empty",
        country="TR",
        now=100,
    )
    service = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )

    report = service.release_gate(
        gate_id="g1",
        club_id="c1",
        tests_passed=True,
        documentation_ready=True,
        now=101,
    )

    assert report.overall_status == "NO_GO"
    assert len(report.blockers) >= 2
