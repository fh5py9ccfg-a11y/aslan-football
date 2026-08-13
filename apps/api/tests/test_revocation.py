from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_revoked_token_is_rejected():
    token = client.post("/auth/dev-token").json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    assert client.post("/auth/revoke", headers=headers).status_code == 200
    assert client.get(
        "/fixtures/revoked/state",
        headers=headers,
    ).status_code == 401
