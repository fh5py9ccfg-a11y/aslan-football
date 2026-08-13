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

class EloModel:
    def __init__(self, k_factor: float = 20.0, home_advantage: float = 60.0):
        if k_factor <= 0:
            raise ValueError("k_factor pozitif olmalıdır")
        self.k_factor = k_factor
        self.home_advantage = home_advantage

    def expected_home_score(self, home_rating, away_rating):
        return 1.0 / (1.0 + pow(
            10.0, (away_rating - (home_rating + self.home_advantage)) / 400.0
        ))

    def update(self, home_rating, away_rating, home_goals, away_goals):
        if min(home_goals, away_goals) < 0:
            raise ValueError("Gol sayıları negatif olamaz")
        eh = self.expected_home_score(home_rating, away_rating)
        ea = 1.0 - eh
        ah, aa = ((1.0, 0.0) if home_goals > away_goals else
                  (0.0, 1.0) if home_goals < away_goals else (0.5, 0.5))
        multiplier = 1.0 + min(abs(home_goals-away_goals), 4) * 0.1
        return EloUpdate(
            home_rating, away_rating,
            home_rating + self.k_factor * multiplier * (ah - eh),
            away_rating + self.k_factor * multiplier * (aa - ea),
            eh, ea,
        )
