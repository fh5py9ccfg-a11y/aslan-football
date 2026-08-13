from apps.api.app.pilot_stabilization import (
    PilotStabilizationService,
)
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


def build():
    redis = Redis()
    workspace = MVPWorkspaceService(
        repository=RedisMVPRepository(
            redis,
            prefix="mvp",
        )
    )
    workspace.create_club(
        club_id="c1",
        name="Aslan",
        country="TR",
        now=100,
    )
    workspace.create_player(
        player_id="p1",
        club_id="c1",
        name="Oyuncu",
        position="ST",
        age=22,
        market_value=3,
        now=100,
    )
    intelligence = MatchIntelligenceService(
        repository=RedisMatchIntelligenceRepository(
            redis,
            prefix="intel",
        ),
        workspace_service=workspace,
    )
    service = PilotStabilizationService(
        workspace_service=workspace,
        intelligence_service=intelligence,
    )
    return service


def test_backup_and_restore_validation():
    service = build()
    backup = service.create_backup(
        backup_id="b1",
        club_id="c1",
        now=101,
    )
    validation = service.validate_restore(
        validation_id="v1",
        backup_id=backup.backup_id,
        payload_json=backup.payload_json,
        expected_checksum=backup.checksum,
        now=102,
    )

    assert backup.entity_counts["players"] == 1
    assert validation.restorable is True
    assert validation.errors == ()


def test_contract_snapshot_deterministic():
    service = build()
    one = service.contract_snapshot(
        snapshot_id="s1",
        api_version="build-016",
        routes=("/b", "/a", "/a"),
        now=101,
    )
    two = service.contract_snapshot(
        snapshot_id="s2",
        api_version="build-016",
        routes=("/a", "/b"),
        now=102,
    )

    assert one.routes == ("/a", "/b")
    assert one.checksum == two.checksum
