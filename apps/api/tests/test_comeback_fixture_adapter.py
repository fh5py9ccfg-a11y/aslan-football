import json
from types import SimpleNamespace

from app.comeback_fixture_adapter import (
    REQUIRED_MARKET_FIELDS,
    comeback_data_readiness,
    fixture_to_comeback_payload,
)


def _fixture(raw):
    return SimpleNamespace(
        fixture_id="fx-1",
        provider="sportmonks",
        provider_fixture_id="1001",
        league_name="Test League",
        home_team="Home",
        away_team="Away",
        kickoff_at=None,
        status="scheduled",
        raw_json=json.dumps(raw),
    )


def test_adapter_marks_complete_enrichment_ready():
    values = {
        "home_win_probability": 0.58,
        "draw_probability": 0.24,
        "away_win_probability": 0.18,
        "first_half_home_probability": 0.34,
        "first_half_draw_probability": 0.40,
        "first_half_away_probability": 0.26,
    }
    payload = fixture_to_comeback_payload(
        _fixture({"comeback_inputs": values})
    )

    assert payload["data_ready"] is True
    assert payload["missing_fields"] == []
    assert payload["comeback_inputs"]["home_win_probability"] == 0.58


def test_adapter_does_not_invent_missing_market_data():
    payload = fixture_to_comeback_payload(
        _fixture({"name": "ordinary provider fixture"})
    )

    assert payload["data_ready"] is False
    assert set(payload["missing_fields"]) == set(REQUIRED_MARKET_FIELDS)
    assert payload["comeback_inputs"] == {}


def test_readiness_counts_missing_fields():
    items = [
        {"data_ready": True, "missing_fields": []},
        {
            "data_ready": False,
            "missing_fields": ["home_win_probability", "draw_probability"],
        },
    ]
    result = comeback_data_readiness(items)

    assert result["fixtures"] == 2
    assert result["ready"] == 1
    assert result["not_ready"] == 1
    assert result["ready_ratio"] == 0.5
    assert result["missing_counts"]["home_win_probability"] == 1
