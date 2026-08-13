from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PayloadValidationResult:
    valid: bool
    errors: tuple[str, ...]
    warnings: tuple[str, ...]

@dataclass(frozen=True)
class NormalizedFixturePayload:
    fixture_id: str
    league_id: str | None
    season_id: str | None
    home_team_id: str
    away_team_id: str
    state: str
    minute: int | None
    home_score: int | None
    away_score: int | None
    starting_at: str | None
    raw: dict

@dataclass(frozen=True)
class NormalizedPlayerPayload:
    player_id: str
    name: str
    team_id: str | None
    position_id: str | None
    nationality_id: str | None
    date_of_birth: str | None
    raw: dict

@dataclass(frozen=True)
class NormalizedProviderEvent:
    event_id: str
    fixture_id: str
    team_id: str | None
    player_id: str | None
    event_type: str
    minute: int
    extra_minute: int | None
    cancelled: bool
    raw: dict
