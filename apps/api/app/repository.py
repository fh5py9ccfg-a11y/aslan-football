from __future__ import annotations
from collections import defaultdict
from threading import Lock
from football_core import MatchEvent

class InMemoryEventRepository:
    def __init__(self):
        self._items = defaultdict(list)
        self._lock = Lock()

    def append(self, event: MatchEvent) -> bool:
        with self._lock:
            if any(item.sequence == event.sequence for item in self._items[event.fixture_id]):
                return False
            self._items[event.fixture_id].append(event)
            return True

    def list(self, fixture_id: str) -> list[MatchEvent]:
        with self._lock:
            return list(self._items[fixture_id])

event_repository = InMemoryEventRepository()
