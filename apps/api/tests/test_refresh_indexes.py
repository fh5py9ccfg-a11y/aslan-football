from apps.api.app.refresh_sessions import (
    InMemoryRefreshSessionRepository,
)

def test_family_and_subject_indexes():
    repo = InMemoryRefreshSessionRepository()

    _, first = repo.issue(
        subject="user-a",
        roles=("viewer",),
    )
    _, second = repo.issue(
        subject="user-a",
        roles=("viewer",),
    )

    listed = repo.list_subject("user-a")
    assert {
        item.session_id
        for item in listed
    } == {
        first.session_id,
        second.session_id,
    }

    assert repo.revoke_family(
        first.family_id
    ) == 1

    first_after = repo.get(first.session_id)
    second_after = repo.get(second.session_id)

    assert first_after is not None
    assert first_after.status == "REVOKED"

    assert second_after is not None
    assert second_after.status == "ACTIVE"
