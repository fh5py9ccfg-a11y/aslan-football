from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_session_listing_revoke_and_logout_all():
    first = client.post(
        "/auth/dev-token",
        headers={"User-Agent": "device-one"},
    ).json()
    second = client.post(
        "/auth/dev-token",
        headers={"User-Agent": "device-two"},
    ).json()

    headers = {
        "Authorization": (
            f"Bearer {first['access_token']}"
        )
    }

    sessions = client.get(
        "/auth/sessions",
        headers=headers,
    )
    assert sessions.status_code == 200
    assert len(sessions.json()) >= 2

    revoke = client.post(
        f"/auth/sessions/"
        f"{second['refresh_session_id']}/revoke",
        headers=headers,
    )
    assert revoke.status_code == 200
    assert revoke.json()["status"] == "REVOKED"

    logout = client.post(
        "/auth/logout-all",
        headers=headers,
    )
    assert logout.status_code == 200
    assert logout.json()["revoked_sessions"] >= 1
