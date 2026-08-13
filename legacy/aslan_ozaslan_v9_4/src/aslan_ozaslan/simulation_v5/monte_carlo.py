from __future__ import annotations
from dataclasses import dataclass

from .domain import MatchSimulationInput, MatchState
from .event_engine import MatchEventSimulator

@dataclass(frozen=True)
class MatchSimulationReport:
    iterations: int
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    average_home_goals: float
    average_away_goals: float
    home_red_card_probability: float
    away_red_card_probability: float
    most_common_score: tuple[int, int]

class MonteCarloMatchSimulator:
    def __init__(self, simulator: MatchEventSimulator | None = None):
        self.simulator = simulator or MatchEventSimulator()

    def run(
        self,
        item: MatchSimulationInput,
        *,
        iterations: int = 10000,
        seed: int = 1,
        starting_state: MatchState | None = None,
    ) -> MatchSimulationReport:
        if iterations <= 0:
            raise ValueError("iterations pozitif olmalıdır")

        home_wins = draws = away_wins = 0
        home_goals_total = away_goals_total = 0
        home_red_total = away_red_total = 0
        score_counts: dict[tuple[int, int], int] = {}

        for index in range(iterations):
            match = self.simulator.simulate(
                item,
                seed=seed + index,
                starting_state=starting_state,
            )
            home_wins += int(match.winner == "HOME")
            draws += int(match.winner == "DRAW")
            away_wins += int(match.winner == "AWAY")
            home_goals_total += match.home_goals
            away_goals_total += match.away_goals
            home_red_total += int(match.home_red_cards > 0)
            away_red_total += int(match.away_red_cards > 0)
            score = (match.home_goals, match.away_goals)
            score_counts[score] = score_counts.get(score, 0) + 1

        most_common_score = max(
            score_counts,
            key=lambda score: (score_counts[score], -sum(score), -score[0]),
        )

        return MatchSimulationReport(
            iterations=iterations,
            home_win_probability=home_wins / iterations,
            draw_probability=draws / iterations,
            away_win_probability=away_wins / iterations,
            average_home_goals=home_goals_total / iterations,
            average_away_goals=away_goals_total / iterations,
            home_red_card_probability=home_red_total / iterations,
            away_red_card_probability=away_red_total / iterations,
            most_common_score=most_common_score,
        )
