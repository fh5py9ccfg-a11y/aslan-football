from __future__ import annotations

from datetime import date

# Public market snapshots verified on 2026-08-22.
# Values are normalized implied probabilities from decimal 1X2 odds.
# Sources used when added:
# - SportyTrader Corum FK-Kasimpasa (FT 2.49/3.79/2.75, HT 3.10/2.20/3.40)
# - SportyTrader Fenerbahce-Konyaspor (FT 1.29/6.43/10.20, HT 1.65/2.70/7.60)
_SEEDS = {
    "2026-08-22": [
        {
            "fixture_id": "public:corum-kasimpasa:2026-08-22",
            "provider": "public_market_fallback",
            "home_team": "Corum",
            "away_team": "Kasimpasa",
            "kickoff": "2026-08-22T12:00:00+03:00",
            "status": "scheduled",
            "bulletin_verified": True,
            "market_source": "SportyTrader",
            "comeback_inputs": {
                "home_win_probability": 0.390252,
                "draw_probability": 0.256392,
                "away_win_probability": 0.353355,
                "first_half_home_probability": 0.301127,
                "first_half_draw_probability": 0.424316,
                "first_half_away_probability": 0.274557,
            },
            "data_ready": True,
            "missing_fields": [],
        },
        {
            "fixture_id": "public:fenerbahce-konyaspor:2026-08-22",
            "provider": "public_market_fallback",
            "home_team": "Fenerbahce",
            "away_team": "Konyaspor",
            "kickoff": "2026-08-22T14:30:00+03:00",
            "status": "scheduled",
            "bulletin_verified": True,
            "market_source": "SportyTrader",
            "comeback_inputs": {
                "home_win_probability": 0.753527,
                "draw_probability": 0.151174,
                "away_win_probability": 0.095299,
                "first_half_home_probability": 0.546981,
                "first_half_draw_probability": 0.334266,
                "first_half_away_probability": 0.118752,
            },
            "data_ready": True,
            "missing_fields": [],
        },
    ]
}


def verified_market_fallback(day: date) -> list[dict]:
    return [dict(item) for item in _SEEDS.get(day.isoformat(), ())]
