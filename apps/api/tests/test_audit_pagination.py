from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def auth_headers():
    token = client.post(
        "/auth/dev-token"
    ).json()["access_token"]
    return {
        "Authorization": f"Bearer {token}"
    }

def test_audit_filter_and_pagination():
    headers = auth_headers()

    for sequence in (10, 11):
        client.post(
            "/fixtures/filter-fixture/events",
            headers=headers,
            json={
                "fixture_id": "filter-fixture",
                "sequence": sequence,
                "event_type": "TICK",
                "minute": sequence,
                "team": None,
            },
        )

    response = client.get(
        "/audit",
        headers=headers,
        params={
            "resource": "filter-fixture",
            "outcome": "accepted",
            "limit": 1,
            "offset": 0,
        },
    )
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["resource"] == "filter-fixture"
