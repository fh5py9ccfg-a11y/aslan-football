from apps.api.app.comeback_neighbors import HistoricalMarketRow, evidence_from_pool


def _inputs(home=.50, draw=.28, away=.22, fh_home=.38, fh_draw=.36, fh_away=.26):
    return {
        "home_win_probability": home,
        "draw_probability": draw,
        "away_win_probability": away,
        "first_half_home_probability": fh_home,
        "first_half_draw_probability": fh_draw,
        "first_half_away_probability": fh_away,
    }


def test_neighbor_engine_counts_real_reversal_outcomes():
    target = _inputs()
    vector = tuple(target[key] for key in (
        "home_win_probability", "draw_probability", "away_win_probability",
        "first_half_home_probability", "first_half_draw_probability", "first_half_away_probability",
    ))
    pool = [
        HistoricalMarketRow("a", vector, "AWAY", "HOME"),
        HistoricalMarketRow("b", vector, "HOME", "AWAY"),
        HistoricalMarketRow("c", vector, "DRAW", "HOME"),
    ]
    evidence = evidence_from_pool(target, pool, neighbors=10, max_distance=.05)
    assert evidence.matches == 3
    assert evidence.two_one_matches == 1
    assert evidence.one_two_matches == 1
    assert round(evidence.two_one_rate, 4) == 0.3333
    assert round(evidence.one_two_rate, 4) == 0.3333


def test_neighbor_engine_rejects_distant_profiles():
    target = _inputs()
    distant = (.10, .20, .70, .10, .20, .70)
    pool = [HistoricalMarketRow("x", distant, "AWAY", "HOME")]
    evidence = evidence_from_pool(target, pool, max_distance=.05)
    assert evidence.matches == 0
    assert evidence.two_one_rate == 0.0
    assert evidence.one_two_rate == 0.0
