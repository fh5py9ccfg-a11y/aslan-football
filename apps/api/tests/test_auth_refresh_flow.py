from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_refresh_and_signing_key_rotation():
    issued = client.post("/auth/dev-token").json()
    response = client.post(
        "/auth/refresh",
        params={"refresh_token": issued["refresh_token"]},
    )
    assert response.status_code == 200
    assert response.json()["rotation"] == 1

    replay = client.post(
        "/auth/refresh",
        params={"refresh_token": issued["refresh_token"]},
    )
    assert replay.status_code == 401

    headers = {
        "Authorization": f"Bearer {issued['access_token']}"
    }
    rotated = client.post(
        "/admin/signing-keys/local-v2/activate",
        headers=headers,
        params={
            "secret": "new-signing-secret-at-least-sixteen"
        },
    )
    assert rotated.status_code == 200
    assert rotated.json()["active_key_id"] == "local-v2"
