import pytest

from apps.api.app.identity_gateway import IdentityGateway
from apps.api.app.jwt_tokens import (
    JwtTokenService,
    SigningKeyRing,
)

class FakeOidc:
    def verify(self, token):
        if token != "oidc-token":
            raise ValueError("invalid")
        class Principal:
            subject = "oidc-user"
            roles = ("viewer",)
            token_id = "oidc-jti"
            expires_at = 9999999999
        return Principal()

def test_identity_gateway_local_then_oidc_fallback():
    ring = SigningKeyRing()
    ring.add(
        key_id="local",
        secret="local-secret-at-least-sixteen",
        activate=True,
    )
    local = JwtTokenService(
        key_ring=ring,
        issuer="local",
        audience="api",
    )
    gateway = IdentityGateway(
        local_service=local,
        oidc_verifier=FakeOidc(),
    )

    local_token = local.issue_access_token(
        subject="local-user",
        roles=("admin",),
    )
    assert gateway.verify(local_token).provider == "local"
    assert gateway.verify("oidc-token").provider == "oidc"

    with pytest.raises(ValueError):
        gateway.verify("bad-token")
