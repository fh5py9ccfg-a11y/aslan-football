import pytest

from apps.api.app.refresh_sessions import (
    InMemoryRefreshSessionRepository,
    RefreshReuseDetected,
)

def test_reuse_revokes_token_family():
    repository = InMemoryRefreshSessionRepository()
    original, session = repository.issue(
        subject="user",
        roles=("viewer",),
        ttl_seconds=100,
    )

    rotated, _ = repository.rotate(
        original,
        now=0,
    )

    with pytest.raises(RefreshReuseDetected):
        repository.rotate(
            original,
            now=0,
        )

    current = repository.get(
        session.session_id
    )
    assert current is not None
    assert current.status == "REVOKED"

    with pytest.raises(ValueError):
        repository.rotate(
            rotated,
            now=0,
        )
