from dataclasses import dataclass
import secrets
import time
from threading import Lock

@dataclass(frozen=True)
class WebSocketTicket:
    ticket: str
    subject: str
    roles: tuple[str, ...]
    expires_at: int

class InMemoryWebSocketTicketRepository:
    def __init__(self):
        self._items = {}
        self._lock = Lock()

    def issue(self, *, subject, roles, ttl_seconds=30):
        item = WebSocketTicket(
            ticket=secrets.token_urlsafe(24),
            subject=subject,
            roles=tuple(roles),
            expires_at=int(time.time()) + ttl_seconds,
        )
        with self._lock:
            self._items[item.ticket] = item
        return item

    def consume(self, ticket, *, now=None):
        current = int(now if now is not None else time.time())
        with self._lock:
            item = self._items.pop(ticket, None)
        if item is None or item.expires_at <= current:
            return None
        return item
