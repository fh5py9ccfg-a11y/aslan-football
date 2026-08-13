from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class League:
    league_id: str
    name: str
    country: str
    season: str

@dataclass(frozen=True)
class Team:
    team_id: str
    league_id: str
    name: str

@dataclass(frozen=True)
class MatchResult:
    match_id: str
    league_id: str
    season: str
    played_at: datetime
    home_team_id: str
    away_team_id: str
    home_goals: int
    away_goals: int

    def validate(self) -> None:
        if self.home_goals < 0 or self.away_goals < 0:
            raise ValueError("Gol sayıları negatif olamaz")
        if self.home_team_id == self.away_team_id:
            raise ValueError("Bir takım kendisiyle oynayamaz")
        if self.played_at.tzinfo is None:
            raise ValueError("played_at timezone içermelidir")
