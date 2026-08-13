from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any


@dataclass(frozen=True)
class TelemetryEvent:
    name: str
    timestamp: str
    attributes: dict[str, Any]


class TelemetryBuffer:
    def __init__(self, max_events: int = 1000):
        if max_events <= 0:
            raise ValueError("max_events pozitif olmalıdır")
        self.max_events = max_events
        self._events: list[TelemetryEvent] = []

    def emit(self, name: str, attributes: dict[str, Any]) -> TelemetryEvent:
        if not name.strip():
            raise ValueError("Telemetry event adı boş olamaz")
        event = TelemetryEvent(
            name=name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            attributes=dict(attributes),
        )
        self._events.append(event)
        if len(self._events) > self.max_events:
            self._events = self._events[-self.max_events:]
        return event

    def snapshot(self) -> tuple[TelemetryEvent, ...]:
        return tuple(self._events)
