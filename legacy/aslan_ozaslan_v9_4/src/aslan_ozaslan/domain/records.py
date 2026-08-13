from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class FixtureRecord:
    fixture_id: str
    provider: str
    competition_id: str
    season: str
    kickoff_at: datetime
    home_team_id: str
    away_team_id: str
    status: str
    observed_at: datetime


@dataclass(frozen=True)
class TeamSnapshot:
    provider: str
    team_id: str
    competition_id: str
    observed_at: datetime
    matches_played: int
    goals_for: int
    goals_against: int
    home_matches: int
    away_matches: int
    injuries_known: bool
    lineup_known: bool
