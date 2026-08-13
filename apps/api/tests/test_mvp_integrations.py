from apps.api.app.mvp_integrations import (
    MVPIntegrationService,
    RedisMVPIntegrationRepository,
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
    service = MVPIntegrationService(
        repository=RedisMVPIntegrationRepository(
            redis,
            prefix="integrations",
        ),
        workspace_service=workspace,
    )
    workspace.create_club(
        club_id="c1",
        name="Club",
        country="TR",
        now=100,
    )
    return workspace, service


def test_player_csv_import_and_duplicate_skip():
    workspace, service = build()
    csv_text = (
        "player_id,name,position,age,market_value\n"
        "p1,Ali,ST,22,3.5\n"
        "p2,Veli,CM,23,2.0\n"
    )

    first = service.import_players_csv(
        sync_id="s1",
        club_id="c1",
        csv_text=csv_text,
        now=101,
    )
    second = service.import_players_csv(
        sync_id="s2",
        club_id="c1",
        csv_text=csv_text,
        now=102,
    )

    assert first.status == "COMPLETED"
    assert first.imported == 2
    assert second.skipped == 2
    assert len(
        workspace.repository.list_players("c1")
    ) == 2


def test_fixture_csv_partial_error_report():
    workspace, service = build()
    csv_text = (
        "match_id,opponent,competition,kickoff_at,venue\n"
        "m1,Rakip,Lig,1000,HOME\n"
        "m2,Rakip 2,Lig,not-a-number,AWAY\n"
    )

    result = service.import_fixtures_csv(
        sync_id="s1",
        club_id="c1",
        csv_text=csv_text,
        now=101,
    )

    assert result.status == "PARTIAL"
    assert result.imported == 1
    assert result.failed == 1
    assert len(result.errors) == 1
