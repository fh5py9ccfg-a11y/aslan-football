from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LeagueParameters:
    competition_id: str
    league_goal_average: float
    home_advantage_multiplier: float
    elo_k_factor: float
    minimum_team_samples: int
    active: bool = True

class LeagueParameterRegistry:
    def __init__(self):
        self._items: dict[str, LeagueParameters] = {}

    def register(self, parameters: LeagueParameters) -> None:
        if parameters.league_goal_average <= 0:
            raise ValueError("league_goal_average pozitif olmalıdır")
        if parameters.home_advantage_multiplier <= 0:
            raise ValueError("home_advantage_multiplier pozitif olmalıdır")
        if parameters.elo_k_factor <= 0:
            raise ValueError("elo_k_factor pozitif olmalıdır")
        if parameters.minimum_team_samples <= 0:
            raise ValueError("minimum_team_samples pozitif olmalıdır")
        self._items[parameters.competition_id] = parameters

    def get(self, competition_id: str) -> LeagueParameters:
        try:
            parameters = self._items[competition_id]
        except KeyError as exc:
            raise LookupError(f"Lig parametresi bulunamadı: {competition_id}") from exc
        if not parameters.active:
            raise RuntimeError(f"Lig analiz için aktif değil: {competition_id}")
        return parameters
