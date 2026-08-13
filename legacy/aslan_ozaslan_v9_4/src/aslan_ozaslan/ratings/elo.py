from __future__ import annotations
from dataclasses import dataclass
from math import pow

@dataclass(frozen=True)
class EloUpdate:
    home_before: float
    away_before: float
    home_after: float
    away_after: float
    expected_home: float
    expected_away: float

class EloRatingSystem:
    def __init__(self, k_factor: float = 20.0, home_advantage: float = 60.0):
        if k_factor <= 0:
            raise ValueError("k_factor pozitif olmalıdır")
        self.k_factor = float(k_factor)
        self.home_advantage = float(home_advantage)

    def expected_scores(self, home_rating: float, away_rating: float) -> tuple[float, float]:
        adjusted_home = home_rating + self.home_advantage
        expected_home = 1.0 / (1.0 + pow(10.0, (away_rating - adjusted_home) / 400.0))
        expected_away = 1.0 - expected_home
        return expected_home, expected_away

    def update(self, home_rating: float, away_rating: float, outcome: str) -> EloUpdate:
        if outcome not in {"HOME", "DRAW", "AWAY"}:
            raise ValueError("outcome HOME, DRAW veya AWAY olmalıdır")
        expected_home, expected_away = self.expected_scores(home_rating, away_rating)
        actual_home = 1.0 if outcome == "HOME" else 0.5 if outcome == "DRAW" else 0.0
        actual_away = 1.0 - actual_home
        return EloUpdate(
            home_before=home_rating,
            away_before=away_rating,
            home_after=round(home_rating + self.k_factor * (actual_home - expected_home), 4),
            away_after=round(away_rating + self.k_factor * (actual_away - expected_away), 4),
            expected_home=round(expected_home, 6),
            expected_away=round(expected_away, 6),
        )
