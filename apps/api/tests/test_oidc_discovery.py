import httpx
import pytest

from apps.api.app.oidc_discovery import (
    OidcDiscoveryCache,
)

def test_oidc_discovery_cache():
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return httpx.Response(
            200,
            json={
                "issuer": "https://issuer.test",
                "jwks_uri": "https://issuer.test/jwks",
                "authorization_endpoint": (
                    "https://issuer.test/authorize"
                ),
                "token_endpoint": (
                    "https://issuer.test/token"
                ),
                "scopes_supported": [
                    "openid",
                    "profile",
                ],
                "response_types_supported": [
                    "code",
                ],
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler)
    )
    cache = OidcDiscoveryCache(
        issuer="https://issuer.test",
        ttl_seconds=60,
        client=client,
    )

    first = cache.get(now=0)
    second = cache.get(now=30)

    assert first.jwks_uri == "https://issuer.test/jwks"
    assert second.token_endpoint == "https://issuer.test/token"
    assert calls["count"] == 1

    cache.get(now=61)
    assert calls["count"] == 2
    client.close()

def test_discovery_issuer_mismatch_rejected():
    client = httpx.Client(
        transport=httpx.MockTransport(
            lambda request: httpx.Response(
                200,
                json={
                    "issuer": "https://evil.test",
                    "jwks_uri": "https://evil.test/jwks",
                },
            )
        )
    )
    cache = OidcDiscoveryCache(
        issuer="https://issuer.test",
        client=client,
    )
    with pytest.raises(ValueError):
        cache.get(now=0)
    client.close()
