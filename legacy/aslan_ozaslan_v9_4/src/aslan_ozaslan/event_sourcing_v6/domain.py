from dataclasses import dataclass

@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    fixture_id: str
    sequence: int
    event_type: str
    occurred_at: str
    payload: dict
    correlation_id: str | None = None
    causation_id: str | None = None
    metadata: dict | None = None

    def validate(self):
        if not self.event_id.strip() or not self.fixture_id.strip():
            raise ValueError("event_id ve fixture_id boş olamaz")
        if self.sequence < 0:
            raise ValueError("sequence negatif olamaz")
        if not self.event_type.strip():
            raise ValueError("event_type boş olamaz")

@dataclass(frozen=True)
class MatchAggregateState:
    fixture_id: str
    last_sequence: int
    minute: int
    home_team_id: str
    away_team_id: str
    home_goals: int
    away_goals: int
    home_red_cards: int
    away_red_cards: int
    processed_events: int

@dataclass(frozen=True)
class AggregateSnapshot:
    fixture_id: str
    last_sequence: int
    state: MatchAggregateState
