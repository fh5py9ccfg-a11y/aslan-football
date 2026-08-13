from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_refresh_reuse_endpoint_revokes_family():
    issued = client.post(
        "/auth/dev-token"
    ).json()

    refreshed = client.post(
        "/auth/refresh",
        params={
            "refresh_token": issued[
                "refresh_token"
            ]
        },
    )
    assert refreshed.status_code == 200

    replay = client.post(
        "/auth/refresh",
        params={
            "refresh_token": issued[
                "refresh_token"
            ]
        },
    )
    assert replay.status_code == 401
    assert "reuse" in replay.json()["detail"].lower()

    current = client.post(
        "/auth/refresh",
        params={
            "refresh_token": refreshed.json()[
                "refresh_token"
            ]
        },
    )
    assert current.status_code == 401
