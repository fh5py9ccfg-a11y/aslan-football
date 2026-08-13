from __future__ import annotations
from dataclasses import dataclass
from math import exp, factorial

@dataclass(frozen=True)
class ScoreDistribution:
    home_win: float
    draw: float
    away_win: float
    home_expected_goals: float
    away_expected_goals: float
    scorelines: tuple[tuple[int, int, float], ...]

class PoissonScoreModel:
    def __init__(self, max_goals: int = 8):
        if max_goals < 3:
            raise ValueError("max_goals en az 3 olmalıdır")
        self.max_goals = int(max_goals)

    def _pmf(self, goals: int, lam: float) -> float:
        if lam <= 0:
            raise ValueError("Beklenen gol pozitif olmalıdır")
        return exp(-lam) * (lam ** goals) / factorial(goals)

    def predict(self, home_xg: float, away_xg: float) -> ScoreDistribution:
        if home_xg <= 0 or away_xg <= 0:
            raise ValueError("Beklenen goller pozitif olmalıdır")

        home_probs = [self._pmf(i, home_xg) for i in range(self.max_goals + 1)]
        away_probs = [self._pmf(i, away_xg) for i in range(self.max_goals + 1)]

        scorelines = []
        home_win = draw = away_win = 0.0
        total_mass = 0.0

        for home_goals, hp in enumerate(home_probs):
            for away_goals, ap in enumerate(away_probs):
                probability = hp * ap
                total_mass += probability
                scorelines.append((home_goals, away_goals, probability))
                if home_goals > away_goals:
                    home_win += probability
                elif home_goals == away_goals:
                    draw += probability
                else:
                    away_win += probability

        if total_mass <= 0:
            raise RuntimeError("Olasılık kütlesi hesaplanamadı")

        home_win /= total_mass
        draw /= total_mass
        away_win /= total_mass
        normalized_scores = tuple(
            sorted(
                (
                    (h, a, round(p / total_mass, 8))
                    for h, a, p in scorelines
                ),
                key=lambda item: (-item[2], item[0], item[1]),
            )
        )

        return ScoreDistribution(
            home_win=round(home_win, 8),
            draw=round(draw, 8),
            away_win=round(away_win, 8),
            home_expected_goals=round(home_xg, 4),
            away_expected_goals=round(away_xg, 4),
            scorelines=normalized_scores,
        )
