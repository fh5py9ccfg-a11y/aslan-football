import pytest

from apps.api.app.claim_mapping import (
    ClaimMapper,
    ClaimMapping,
)
from apps.api.app.oidc import OidcTokenVerifier

class FakeCache:
    pass

def test_allowed_issuer_normalization():
    verifier = OidcTokenVerifier(
        issuer="https://issuer-a.test/",
        audience="api",
        jwks_cache=FakeCache(),
        allowed_issuers=(
            "https://issuer-a.test/",
            "https://issuer-b.test",
        ),
        claim_mapper=ClaimMapper(
            ClaimMapping.from_json(None)
        ),
    )

    assert verifier.allowed_issuers == (
        "https://issuer-a.test",
        "https://issuer-b.test",
    )
