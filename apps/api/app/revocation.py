import time
from threading import Lock

class InMemoryRevocationRepository:
    def __init__(self):
        self._items = {}
        self._lock = Lock()

    def revoke(self, token_id, expires_at):
        with self._lock:
            self._items[token_id] = expires_at

    def is_revoked(self, token_id, now=None):
        current = int(now if now is not None else time.time())
        with self._lock:
            for key, expiry in list(self._items.items()):
                if expiry <= current:
                    self._items.pop(key, None)
            return token_id in self._items
