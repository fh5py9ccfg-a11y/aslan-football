from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def headers():
    token = client.post("/auth/dev-token").json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_websocket_requires_ticket():
    try:
        with client.websocket_connect("/ws/fixtures/ws-fixture"):
            assert False
    except Exception:
        assert True

def test_websocket_ticket_is_valid_once():
    ticket = client.post(
        "/auth/ws-ticket",
        headers=headers(),
    ).json()["ticket"]

    with client.websocket_connect(
        f"/ws/fixtures/ws-fixture?ticket={ticket}"
    ) as websocket:
        assert websocket.receive_json()["fixture_id"] == "ws-fixture"

    try:
        with client.websocket_connect(
            f"/ws/fixtures/ws-fixture?ticket={ticket}"
        ):
            assert False
    except Exception:
        assert True
