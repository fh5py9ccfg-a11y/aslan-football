import time
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

def test_protected_endpoint_requires_token():
    response = client.get("/fixtures/secure-fixture/state")
    assert response.status_code == 401

def test_role_authorization_and_security_headers():
    viewer = app.state.token_service.issue_access_token(
        subject="viewer",
        roles=("viewer",),
        ttl_seconds=300,
    )
    response = client.get(
        "/fixtures/secure-fixture/state",
        headers={"Authorization": f"Bearer {viewer}"},
    )
    assert response.status_code == 200
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["X-Content-Type-Options"] == "nosniff"

    forbidden = client.post(
        "/fixtures/secure-fixture/events",
        headers={"Authorization": f"Bearer {viewer}"},
        json={
            "fixture_id": "secure-fixture",
            "sequence": 1,
            "event_type": "GOAL",
            "minute": 1,
            "team": "HOME",
        },
    )
    assert forbidden.status_code == 403

def test_tampered_token_is_rejected():
    service = app.state.token_service
    token = service.issue_access_token(
        subject="user",
        roles=("viewer",),
        ttl_seconds=300,
    )
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(ValueError):
        service.verify_access_token(tampered)
