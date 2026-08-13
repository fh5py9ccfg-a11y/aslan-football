from __future__ import annotations
from .domain import MatchEvent, MatchState

class MatchStateService:
    def rebuild(
        self,
        fixture_id: str,
        events: list[MatchEvent],
    ) -> MatchState:
        state = MatchState(fixture_id=fixture_id)
        for event in sorted(events, key=lambda item: item.sequence):
            state = state.apply(event)
        return state
