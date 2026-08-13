import os
import pytest
import httpx

pytestmark = pytest.mark.integration

@pytest.mark.skipif(
    os.getenv("RUN_CONTAINER_INTEGRATION") != "1",
    reason="Container integration opt-in",
)
def test_api_health_and_event_flow_over_http():
    base_url = os.getenv("INTEGRATION_API_URL", "http://api:8000")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        health = client.get("/health")
        assert health.status_code == 200

        response = client.post(
            "/fixtures/container-fixture/events",
            json={
                "fixture_id": "container-fixture",
                "sequence": 1,
                "event_type": "GOAL",
                "minute": 8,
                "team": "HOME",
            },
        )
        assert response.status_code in {200, 409}

        state = client.get("/fixtures/container-fixture/state")
        assert state.status_code == 200
        assert state.json()["home_goals"] >= 1
