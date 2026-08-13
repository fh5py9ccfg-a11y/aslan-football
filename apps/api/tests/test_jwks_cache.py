import httpx
import pytest

from apps.api.app.jwks import JwksCache

def test_unknown_kid_triggers_refresh_then_fails():
    calls = {"count": 0}

    def handler(request):
        calls["count"] += 1
        return httpx.Response(
            200,
            json={
                "keys": [{
                    "kid": "known",
                    "kty": "RSA",
                    "alg": "RS256",
                    "n": "AQAB",
                    "e": "AQAB",
                }]
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler)
    )
    cache = JwksCache(
        jwks_url="https://issuer.test/jwks",
        ttl_seconds=30,
        client=client,
    )

    with pytest.raises(ValueError):
        cache.get("missing", now=0)
    assert calls["count"] == 1
    client.close()
