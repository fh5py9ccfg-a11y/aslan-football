import pytest
from apps.api.app.jwt_tokens import JwtTokenService, SigningKeyRing

def test_jwt_rotation_and_audience():
    ring = SigningKeyRing()
    ring.add(
        key_id="v1",
        secret="jwt-secret-at-least-sixteen",
        activate=True,
    )
    service = JwtTokenService(
        key_ring=ring,
        issuer="issuer",
        audience="aud",
    )
    first = service.issue_access_token(
        subject="u1",
        roles=("viewer",),
        ttl_seconds=100,
    )
    assert len(first.split(".")) == 3
    assert service.verify_access_token(first).key_id == "v1"

    ring.add(
        key_id="v2",
        secret="second-secret-at-least-sixteen",
        activate=True,
    )
    second = service.issue_access_token(
        subject="u1",
        roles=("viewer",),
        ttl_seconds=100,
    )
    assert service.verify_access_token(second).key_id == "v2"
    assert service.verify_access_token(first).key_id == "v1"

    wrong = JwtTokenService(
        key_ring=ring,
        issuer="issuer",
        audience="wrong",
    )
    with pytest.raises(ValueError):
        wrong.verify_access_token(second)
