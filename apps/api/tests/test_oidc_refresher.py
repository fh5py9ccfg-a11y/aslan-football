import asyncio

from apps.api.app.oidc_refresh import (
    OidcMetadataRefresher,
)

class FakeCache:
    def __init__(self):
        self.calls = 0

    def get(self, force_refresh=False):
        self.calls += 1

    def refresh(self):
        self.calls += 1

def test_oidc_refresher_run_once():
    discovery = FakeCache()
    jwks = FakeCache()
    refresher = OidcMetadataRefresher(
        discovery_cache=discovery,
        jwks_cache=jwks,
        interval_seconds=10,
    )

    result = asyncio.run(
        refresher.run_once()
    )

    assert result == {
        "discovery": "ok",
        "jwks": "ok",
    }
    assert discovery.calls == 1
    assert jwks.calls == 1
