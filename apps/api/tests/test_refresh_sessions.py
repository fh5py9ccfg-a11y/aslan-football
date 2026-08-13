import pytest
from apps.api.app.refresh_sessions import (
    InMemoryRefreshSessionRepository,
    RefreshReuseDetected,
)

def test_refresh_replay_revokes_family():
    repo = InMemoryRefreshSessionRepository()
    token, session = repo.issue(
        subject="u1",
        roles=("viewer",),
        ttl_seconds=100,
    )

    rotated, rotated_session = repo.rotate(
        token,
        now=0,
    )
    assert rotated_session.rotation == 1

    with pytest.raises(RefreshReuseDetected):
        repo.rotate(
            token,
            now=0,
        )

    current = repo.get(session.session_id)
    assert current is not None
    assert current.status == "REVOKED"

    with pytest.raises(ValueError):
        repo.rotate(
            rotated,
            now=0,
        )
