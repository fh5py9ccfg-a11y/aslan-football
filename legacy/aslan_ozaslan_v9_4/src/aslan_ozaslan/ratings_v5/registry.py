from __future__ import annotations
from dataclasses import dataclass
from .elo import EloModel

@dataclass(frozen=True)
class TeamRating:
    team_id: str
    rating: float
    matches_played: int

class EloRegistry:
    def __init__(self, model=None, initial_rating=1500.0):
        self.model = model or EloModel()
        self.initial_rating = initial_rating
        self._ratings = {}

    def get(self, team_id):
        return self._ratings.get(team_id, TeamRating(team_id, self.initial_rating, 0))

    def apply_result(self, *, home_team_id, away_team_id, home_goals, away_goals):
        home, away = self.get(home_team_id), self.get(away_team_id)
        update = self.model.update(home.rating, away.rating, home_goals, away_goals)
        home_next = TeamRating(home_team_id, update.home_after, home.matches_played + 1)
        away_next = TeamRating(away_team_id, update.away_after, away.matches_played + 1)
        self._ratings[home_team_id], self._ratings[away_team_id] = home_next, away_next
        return home_next, away_next
