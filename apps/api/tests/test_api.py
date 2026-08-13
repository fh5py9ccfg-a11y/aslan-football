from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def auth_headers():
    token = client.post("/auth/dev-token").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

def test_event_flow():
    headers = auth_headers()
    response = client.post(
        "/fixtures/test-fixture/events",
        headers=headers,
        json={
            "fixture_id": "test-fixture",
            "sequence": 1,
            "event_type": "GOAL",
            "minute": 10,
            "team": "HOME",
        },
    )
    assert response.status_code == 200
    assert response.json()["home_goals"] == 1

    duplicate = client.post(
        "/fixtures/test-fixture/events",
        headers=headers,
        json={
            "fixture_id": "test-fixture",
            "sequence": 1,
            "event_type": "GOAL",
            "minute": 10,
            "team": "HOME",
        },
    )
    assert duplicate.status_code == 409
