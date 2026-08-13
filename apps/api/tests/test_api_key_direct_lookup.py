from apps.api.app.api_key_registry import (
    InMemoryApiKeyRegistry,
)

def test_direct_key_id_lookup_and_expired_grace():
    registry = InMemoryApiKeyRegistry()
    registry.upsert(
        key_id="provider-x",
        secret="old-secret-123456",
        roles=("provider",),
    )
    registry.rotate(
        key_id="provider-x",
        new_secret="new-secret-123456",
        grace_seconds=1,
    )

    assert registry.verify(
        key_id="provider-x",
        raw_secret="old-secret-123456",
        now=0,
    ).key_id == "provider-x"

    record = registry.get("provider-x")
    assert record is not None
    assert record.previous_valid_until is not None

    try:
        registry.verify(
            key_id="provider-x",
            raw_secret="old-secret-123456",
            now=record.previous_valid_until + 1,
        )
        assert False
    except ValueError:
        assert True

    assert registry.verify(
        key_id="provider-x",
        raw_secret="new-secret-123456",
    ).version == 2
