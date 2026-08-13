import httpx
import pytest

from apps.api.app.oidc_discovery import (
    OidcDiscoveryCache,
)
from apps.api.app.jwks import JwksCache

class SequencedTransport:
    def __init__(self, responses):
        self.responses = list(responses)

    def __call__(self, request):
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response

def test_discovery_stale_if_error():
    transport = SequencedTransport([
        httpx.Response(
            200,
            json={
                "issuer": "https://issuer.test",
                "jwks_uri": "https://issuer.test/jwks",
            },
        ),
        httpx.ConnectError("offline"),
    ])
    client = httpx.Client(
        transport=httpx.MockTransport(transport)
    )
    cache = OidcDiscoveryCache(
        issuer="https://issuer.test",
        ttl_seconds=10,
        stale_if_error_seconds=100,
        client=client,
    )

    fresh = cache.get(now=0)
    stale = cache.get(now=20)

    assert fresh.jwks_uri == stale.jwks_uri
    assert cache.health(now=20).status == "stale"
    assert cache.health(now=20).last_error is not None
    client.close()

def test_jwks_expired_stale_rejected():
    transport = SequencedTransport([
        httpx.Response(
            200,
            json={
                "keys": [{
                    "kid": "k1",
                    "kty": "RSA",
                    "n": "AQAB",
                    "e": "AQAB",
                }]
            },
        ),
        httpx.ConnectError("offline"),
    ])
    client = httpx.Client(
        transport=httpx.MockTransport(transport)
    )
    cache = JwksCache(
        jwks_url="https://issuer.test/jwks",
        ttl_seconds=10,
        stale_if_error_seconds=5,
        client=client,
    )

    assert cache.get("k1", now=0).kid == "k1"

    with pytest.raises(httpx.ConnectError):
        cache.get("k1", now=20)

    assert cache.health(now=20).status == "expired"
    client.close()
