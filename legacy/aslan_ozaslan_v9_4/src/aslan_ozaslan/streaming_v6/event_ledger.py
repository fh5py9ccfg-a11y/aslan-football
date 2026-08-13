from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LedgerEvent:
    event_id: str
    version: int
    payload: dict
    active: bool

class EventLedger:
    def __init__(self):
        self._events: dict[str, LedgerEvent] = {}

    def apply_event(self, event_id: str, payload: dict) -> LedgerEvent:
        current = self._events.get(event_id)
        version = 1 if current is None else current.version + 1
        updated = LedgerEvent(event_id, version, dict(payload), True)
        self._events[event_id] = updated
        return updated

    def apply_correction(
        self,
        event_id: str,
        payload: dict,
        *,
        active: bool = True,
    ) -> LedgerEvent:
        current = self._events.get(event_id)
        if current is None:
            raise KeyError(f"Düzeltilecek event bulunamadı: {event_id}")
        updated = LedgerEvent(
            event_id=event_id,
            version=current.version + 1,
            payload=dict(payload),
            active=active,
        )
        self._events[event_id] = updated
        return updated

    def get(self, event_id: str) -> LedgerEvent | None:
        return self._events.get(event_id)

    def active_events(self) -> tuple[LedgerEvent, ...]:
        return tuple(
            sorted(
                (item for item in self._events.values() if item.active),
                key=lambda item: item.event_id,
            )
        )
