from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderFixtureSnapshot:
    fixture_id: str
    minute: int
    home_team_id: str
    away_team_id: str
    home_score: int
    away_score: int
    state: str
    updated_at: str

@dataclass(frozen=True)
class AnalyticsUpdate:
    fixture_id: str
    accepted: bool
    reason: str
    home_probability: float | None
    draw_probability: float | None
    away_probability: float | None
    event_count: int
