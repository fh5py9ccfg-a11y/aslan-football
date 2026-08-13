from __future__ import annotations
from pydantic import BaseModel, Field

class EventIn(BaseModel):
    fixture_id: str = Field(min_length=1)
    sequence: int = Field(ge=0)
    event_type: str
    minute: int = Field(ge=0, le=130)
    team: str | None = None

class MatchStateOut(BaseModel):
    fixture_id: str
    last_sequence: int
    minute: int
    home_goals: int
    away_goals: int
    home_red_cards: int
    away_red_cards: int
