from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def auth_headers():
    token = client.post(
        "/auth/dev-token"
    ).json()["access_token"]
    return {
        "Authorization": (
            f"Bearer {token}"
        )
    }

def test_audit_log_records_event():
    headers = auth_headers()
    headers["X-Correlation-ID"] = (
        "audit-corr-1"
    )
    response = client.post(
        "/fixtures/audit-fixture/events",
        headers=headers,
        json={
            "fixture_id": "audit-fixture",
            "sequence": 1,
            "event_type": "GOAL",
            "minute": 3,
            "team": "HOME",
        },
    )
    assert response.status_code == 200

    audit = client.get(
        "/audit",
        headers=headers,
    )
    assert audit.status_code == 200
    items = audit.json()
    assert any(
        item["resource"]
        == "audit-fixture"
        and item["outcome"]
        == "accepted"
        and item["correlation_id"]
        == "audit-corr-1"
        for item in items
    )

def test_request_size_limit():
    headers = auth_headers()
    headers["Content-Length"] = "2000000"
    response = client.post(
        "/fixtures/large/events",
        headers=headers,
        content=b"{}",
    )
    assert response.status_code == 413
