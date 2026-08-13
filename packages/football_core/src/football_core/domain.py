from __future__ import annotations
from dataclasses import dataclass, replace

@dataclass(frozen=True)
class MatchEvent:
    fixture_id: str
    sequence: int
    event_type: str
    minute: int
    team: str | None = None

    def validate(self) -> None:
        if not self.fixture_id.strip():
            raise ValueError("fixture_id boş olamaz")
        if self.sequence < 0:
            raise ValueError("sequence negatif olamaz")
        if not 0 <= self.minute <= 130:
            raise ValueError("minute geçersiz")
        if self.event_type not in {"GOAL", "RED_CARD", "TICK"}:
            raise ValueError("event_type desteklenmiyor")
        if self.team not in {None, "HOME", "AWAY"}:
            raise ValueError("team geçersiz")

@dataclass(frozen=True)
class MatchState:
    fixture_id: str
    last_sequence: int = -1
    minute: int = 0
    home_goals: int = 0
    away_goals: int = 0
    home_red_cards: int = 0
    away_red_cards: int = 0

    def apply(self, event: MatchEvent) -> "MatchState":
        event.validate()
        if event.fixture_id != self.fixture_id:
            raise ValueError("event farklı fixture'a ait")
        if event.sequence <= self.last_sequence:
            raise ValueError("sequence ilerlemeli")

        values = {
            "last_sequence": event.sequence,
            "minute": max(self.minute, event.minute),
        }
        if event.event_type == "GOAL" and event.team == "HOME":
            values["home_goals"] = self.home_goals + 1
        elif event.event_type == "GOAL" and event.team == "AWAY":
            values["away_goals"] = self.away_goals + 1
        elif event.event_type == "RED_CARD" and event.team == "HOME":
            values["home_red_cards"] = self.home_red_cards + 1
        elif event.event_type == "RED_CARD" and event.team == "AWAY":
            values["away_red_cards"] = self.away_red_cards + 1

        return replace(self, **values)
