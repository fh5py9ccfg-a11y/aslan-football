from app.comeback_scanner import ComebackScanner


def _fixture(fixture_id: str, market: str, strength: float):
    if market == "2/1":
        inputs = {
            "home_win_probability": 0.62,
            "draw_probability": 0.22,
            "away_win_probability": 0.16,
            "first_half_home_probability": 0.35,
            "first_half_draw_probability": 0.39,
            "first_half_away_probability": 0.26,
            "home_comeback_rate_when_behind": strength,
            "away_loss_rate_when_ahead": strength * 0.75,
            "home_second_half_goal_share": 0.67,
            "historical_2_1_rate": 0.12,
            "similar_matches": 35,
            "similar_2_1_rate": 0.15,
        }
    else:
        inputs = {
            "home_win_probability": 0.17,
            "draw_probability": 0.23,
            "away_win_probability": 0.60,
            "first_half_home_probability": 0.27,
            "first_half_draw_probability": 0.40,
            "first_half_away_probability": 0.33,
            "away_comeback_rate_when_behind": strength,
            "home_loss_rate_when_ahead": strength * 0.78,
            "away_second_half_goal_share": 0.68,
            "historical_1_2_rate": 0.13,
            "similar_matches": 32,
            "similar_1_2_rate": 0.16,
        }
    return {
        "fixture_id": fixture_id,
        "home_team": f"Home {fixture_id}",
        "away_team": f"Away {fixture_id}",
        "kickoff": "2026-08-22T20:00:00+03:00",
        "comeback_inputs": inputs,
    }


def test_scanner_returns_only_alerts_and_ranks_best_first():
    scanner = ComebackScanner(alert_threshold=68)
    result = scanner.scan([
        _fixture("weak", "2/1", 0.15),
        _fixture("home", "2/1", 0.70),
        _fixture("away", "1/2", 0.63),
    ])

    assert result
    assert result[0]["score"] >= result[-1]["score"]
    assert all(item["preferred_market"] in {"2/1", "1/2"} for item in result)


def test_scanner_skips_fixture_without_required_market_probabilities():
    scanner = ComebackScanner(alert_threshold=50)
    result = scanner.scan([
        {"fixture_id": "missing", "home_team": "A", "away_team": "B"}
    ])
    assert result == []


def test_scanner_limit_is_applied_after_ranking():
    scanner = ComebackScanner(alert_threshold=60)
    fixtures = [
        _fixture("a", "2/1", 0.65),
        _fixture("b", "1/2", 0.67),
        _fixture("c", "2/1", 0.72),
    ]
    result = scanner.scan(fixtures, limit=2)
    assert len(result) == 2
    assert result[0]["score"] >= result[1]["score"]
