import os
os.environ["APP_ENV"] = "test"
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_readiness_and_correlation_headers():
    response = client.get(
        "/ready", headers={"X-Correlation-ID": "corr-123"}
    )
    assert response.status_code == 200
    assert response.json()["ready"] is True
    assert response.headers["X-Correlation-ID"] == "corr-123"
    assert "X-Process-Time-Ms" in response.headers
