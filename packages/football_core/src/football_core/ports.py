from __future__ import annotations
from typing import Protocol
from .domain import MatchEvent

class EventRepository(Protocol):
    def append(self, event: MatchEvent) -> bool: ...
    def list(self, fixture_id: str) -> list[MatchEvent]: ...
