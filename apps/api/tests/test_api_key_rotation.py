import time
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def admin_headers():
    token = client.post(
        "/auth/dev-token"
    ).json()["access_token"]
    return {
        "Authorization": f"Bearer {token}"
    }

def provider_headers(secret):
    return {
        "X-API-Key-ID": "rotating",
        "X-API-Key": secret,
    }

def event(sequence):
    return {
        "fixture_id": "rotation",
        "sequence": sequence,
        "event_type": "TICK",
        "minute": min(sequence, 120),
        "team": None,
    }

def test_api_key_rotation_with_grace_and_revoke():
    registry = app.state.api_key_registry
    registry.upsert(
        key_id="rotating",
        secret="old-secret-123456",
        roles=("provider",),
    )

    assert client.post(
        "/fixtures/rotation/provider-events",
        headers=provider_headers("old-secret-123456"),
        json=event(1),
    ).status_code == 200

    rotate = client.post(
        "/admin/api-keys/rotating/rotate",
        headers=admin_headers(),
        params={
            "new_secret": "new-secret-123456",
            "grace_seconds": 30,
        },
    )
    assert rotate.status_code == 200
    assert rotate.json()["version"] == 2

    assert client.post(
        "/fixtures/rotation/provider-events",
        headers=provider_headers("old-secret-123456"),
        json=event(2),
    ).status_code == 200

    assert client.post(
        "/fixtures/rotation/provider-events",
        headers=provider_headers("new-secret-123456"),
        json=event(3),
    ).status_code == 200

    revoke = client.post(
        "/admin/api-keys/rotating/revoke",
        headers=admin_headers(),
    )
    assert revoke.status_code == 200

    assert client.post(
        "/fixtures/rotation/provider-events",
        headers=provider_headers("new-secret-123456"),
        json=event(4),
    ).status_code == 401
