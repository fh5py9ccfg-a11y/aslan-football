from .domain import LiveMatchEvent
class LiveEventStore:
    def __init__(self): self._events = {}
    def append(self, event: LiveMatchEvent):
        event.validate()
        if event.event_id in self._events: return False
        self._events[event.event_id] = event
        return True
    def ordered(self):
        return tuple(sorted(self._events.values(), key=lambda x:(x.minute,x.event_id)))
    def count(self): return len(self._events)
