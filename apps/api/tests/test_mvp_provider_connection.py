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


def test_provider_connection_and_preview():
    redis = Redis()
    workspace = MVPWorkspaceService(
        repository=RedisMVPRepository(
            redis,
            prefix="mvp",
        )
    )
    workspace.create_club(
        club_id="c1",
        name="Club",
        country="TR",
        now=100,
    )
    service = MVPIntegrationService(
        repository=RedisMVPIntegrationRepository(
            redis,
            prefix="integrations",
        ),
        workspace_service=workspace,
    )
    service.create_connection(
        connection_id="conn1",
        club_id="c1",
        provider="generic_json",
        base_url="https://provider.example",
        external_club_id="ext-1",
        now=101,
    )

    preview = service.provider_payload_preview(
        connection_id="conn1",
        payload_json='{"items":[{"id":"1"},{"id":"2"}]}',
    )

    assert preview["provider"] == "GENERIC_JSON"
    assert preview["record_count"] == 2
