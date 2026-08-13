import base64
import json
import time

import httpx
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from apps.api.app.jwks import JwksCache
from apps.api.app.oidc import OidcTokenVerifier

def b64(data):
    return base64.urlsafe_b64encode(data).decode().rstrip("=")

def int_b64(value):
    size = max(1, (value.bit_length() + 7) // 8)
    return b64(value.to_bytes(size, "big"))

def make_token(private_key, kid, payload):
    header = {"alg": "RS256", "typ": "JWT", "kid": kid}
    head = b64(json.dumps(header, separators=(",", ":")).encode())
    body = b64(json.dumps(payload, separators=(",", ":")).encode())
    signing_input = f"{head}.{body}".encode()
    signature = private_key.sign(
        signing_input,
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return f"{head}.{body}.{b64(signature)}"

def test_rs256_oidc_verification_and_cache():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    public = private_key.public_key().public_numbers()
    requests = {"count": 0}

    def handler(request):
        requests["count"] += 1
        return httpx.Response(
            200,
            json={
                "keys": [{
                    "kid": "rsa-1",
                    "kty": "RSA",
                    "alg": "RS256",
                    "use": "sig",
                    "n": int_b64(public.n),
                    "e": int_b64(public.e),
                }]
            },
        )

    client = httpx.Client(
        transport=httpx.MockTransport(handler)
    )
    cache = JwksCache(
        jwks_url="https://issuer.test/jwks",
        ttl_seconds=300,
        client=client,
    )
    verifier = OidcTokenVerifier(
        issuer="https://issuer.test",
        audience="aslan-api",
        jwks_cache=cache,
    )
    now = int(time.time())
    token = make_token(
        private_key,
        "rsa-1",
        {
            "sub": "oidc-user",
            "roles": ["viewer", "analyst"],
            "iss": "https://issuer.test",
            "aud": "aslan-api",
            "iat": now,
            "nbf": now,
            "exp": now + 300,
            "jti": "oidc-jti",
        },
    )

    principal = verifier.verify(token, now=now)
    assert principal.subject == "oidc-user"
    assert principal.roles == ("viewer", "analyst")
    assert requests["count"] == 1

    verifier.verify(token, now=now)
    assert requests["count"] == 1

    client.close()
