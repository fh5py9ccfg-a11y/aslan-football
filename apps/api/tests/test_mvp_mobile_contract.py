def test_mobile_contract_shape():
    config = {
        "api_version": "build-003",
        "features": [
            "AUTH",
            "DASHBOARD",
            "PLAYERS",
            "MATCHES",
        ],
    }

    assert config["api_version"] == "build-003"
    assert "AUTH" in config["features"]
    assert "PLAYERS" in config["features"]
