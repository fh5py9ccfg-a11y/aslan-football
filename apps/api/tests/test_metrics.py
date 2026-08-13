from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def auth_headers():
    token = client.post("/auth/dev-token").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_metrics_endpoint():
    headers = auth_headers()
    client.post(
        "/fixtures/metrics-fixture/events",
        headers=headers,
        json={
            "fixture_id": "metrics-fixture",
            "sequence": 1,
            "event_type": "GOAL",
            "minute": 5,
            "team": "HOME",
        },
    )
    response = client.get("/metrics", headers=headers)
    assert response.status_code == 200
    assert "aslan_api_event_requests_total" in response.text
