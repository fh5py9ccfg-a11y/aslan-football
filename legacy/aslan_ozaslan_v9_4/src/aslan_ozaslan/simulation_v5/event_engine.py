from __future__ import annotations
from dataclasses import dataclass
import random

from .domain import MatchSimulationInput, MatchState
from .poisson import PoissonSampler

@dataclass(frozen=True)
class SimulatedMatch:
    home_goals: int
    away_goals: int
    home_red_cards: int
    away_red_cards: int
    first_goal_team: str | None
    winner: str

class MatchEventSimulator:
    def __init__(self, sampler: PoissonSampler | None = None):
        self.sampler = sampler or PoissonSampler()

    def simulate(
        self,
        item: MatchSimulationInput,
        *,
        seed: int | None = None,
        starting_state: MatchState | None = None,
    ) -> SimulatedMatch:
        item.validate()
        state = starting_state or MatchState(0, 0, 0, 0, 0)
        state.validate()

        rng = random.Random(seed)
        remaining_ratio = max(0.0, (90 - min(state.minute, 90)) / 90.0)

        home_xg = item.home_expected_goals * remaining_ratio
        away_xg = item.away_expected_goals * remaining_ratio

        home_red = state.home_red_cards + int(
            rng.random() < item.home_red_card_probability * remaining_ratio
        )
        away_red = state.away_red_cards + int(
            rng.random() < item.away_red_card_probability * remaining_ratio
        )

        if home_red > away_red:
            home_xg *= 0.72
            away_xg *= 1.18
        elif away_red > home_red:
            away_xg *= 0.72
            home_xg *= 1.18

        new_home_goals = self.sampler.sample(home_xg, rng)
        new_away_goals = self.sampler.sample(away_xg, rng)

        home_goals = state.home_goals + new_home_goals
        away_goals = state.away_goals + new_away_goals

        if state.home_goals or state.away_goals:
            first_goal_team = (
                item.home_team_id
                if state.home_goals > 0 and state.away_goals == 0
                else item.away_team_id
                if state.away_goals > 0 and state.home_goals == 0
                else None
            )
        elif new_home_goals > 0 and new_away_goals == 0:
            first_goal_team = item.home_team_id
        elif new_away_goals > 0 and new_home_goals == 0:
            first_goal_team = item.away_team_id
        else:
            first_goal_team = None

        winner = (
            "HOME" if home_goals > away_goals
            else "AWAY" if away_goals > home_goals
            else "DRAW"
        )

        return SimulatedMatch(
            home_goals=home_goals,
            away_goals=away_goals,
            home_red_cards=home_red,
            away_red_cards=away_red,
            first_goal_team=first_goal_team,
            winner=winner,
        )
