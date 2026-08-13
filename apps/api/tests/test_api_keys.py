import importlib
from fastapi.testclient import TestClient

def test_provider_api_key_endpoint(monkeypatch):
    monkeypatch.setenv(
        "PROVIDER_API_KEYS",
        "provider-1:secret-key-123",
    )

    import apps.api.app.api_keys as api_keys_module
    import apps.api.app.main as main_module
    importlib.reload(api_keys_module)
    importlib.reload(main_module)

    client = TestClient(main_module.app)
    response = client.post(
        "/fixtures/provider-fixture/provider-events",
        headers={
            "X-API-Key-ID": "provider-1",
            "X-API-Key": "secret-key-123",
        },
        json={
            "fixture_id": "provider-fixture",
            "sequence": 901,
            "event_type": "GOAL",
            "minute": 30,
            "team": "AWAY",
        },
    )
    assert response.status_code == 200
    assert response.json()["away_goals"] == 1
