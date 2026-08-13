from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TeamStrengthInput:
    attack_rating: float
    defense_rating: float
    recent_form_points: float
    elo_rating: float

class ExpectedGoalsEstimator:
    def __init__(self, league_goal_average: float = 1.35, home_advantage_multiplier: float = 1.10):
        if league_goal_average <= 0:
            raise ValueError("league_goal_average pozitif olmalıdır")
        if home_advantage_multiplier <= 0:
            raise ValueError("home_advantage_multiplier pozitif olmalıdır")
        self.league_goal_average = float(league_goal_average)
        self.home_advantage_multiplier = float(home_advantage_multiplier)

    def estimate(
        self,
        home: TeamStrengthInput,
        away: TeamStrengthInput,
    ) -> tuple[float, float]:
        home_attack = max(home.attack_rating, 0.05)
        away_attack = max(away.attack_rating, 0.05)
        home_defense = max(home.defense_rating, 0.05)
        away_defense = max(away.defense_rating, 0.05)

        home_form_factor = 0.85 + min(max(home.recent_form_points / 3.0, 0.0), 1.0) * 0.30
        away_form_factor = 0.85 + min(max(away.recent_form_points / 3.0, 0.0), 1.0) * 0.30

        elo_diff = max(min((home.elo_rating - away.elo_rating) / 400.0, 0.5), -0.5)
        home_elo_factor = 1.0 + 0.20 * elo_diff
        away_elo_factor = 1.0 - 0.20 * elo_diff

        home_xg = (
            self.league_goal_average
            * home_attack
            * away_defense
            * home_form_factor
            * home_elo_factor
            * self.home_advantage_multiplier
        )
        away_xg = (
            self.league_goal_average
            * away_attack
            * home_defense
            * away_form_factor
            * away_elo_factor
        )

        return round(max(home_xg, 0.05), 4), round(max(away_xg, 0.05), 4)
