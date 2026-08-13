from __future__ import annotations
from dataclasses import dataclass

from .monte_carlo import MatchSimulationReport

@dataclass(frozen=True)
class ScenarioDifference:
    home_win_change: float
    draw_change: float
    away_win_change: float
    home_goal_change: float
    away_goal_change: float

class ScenarioComparator:
    def compare(
        self,
        baseline: MatchSimulationReport,
        scenario: MatchSimulationReport,
    ) -> ScenarioDifference:
        return ScenarioDifference(
            home_win_change=(
                scenario.home_win_probability
                - baseline.home_win_probability
            ),
            draw_change=scenario.draw_probability - baseline.draw_probability,
            away_win_change=(
                scenario.away_win_probability
                - baseline.away_win_probability
            ),
            home_goal_change=(
                scenario.average_home_goals
                - baseline.average_home_goals
            ),
            away_goal_change=(
                scenario.average_away_goals
                - baseline.average_away_goals
            ),
        )
