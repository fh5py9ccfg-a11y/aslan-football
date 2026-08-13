from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from threading import RLock


@dataclass(frozen=True)
class LockLease:
    name: str
    owner: str
    expires_at: datetime


class DistributedLock:
    def acquire(self, name: str, owner: str, ttl_seconds: int) -> bool:
        raise NotImplementedError

    def release(self, name: str, owner: str) -> bool:
        raise NotImplementedError


class InMemoryDistributedLock(DistributedLock):
    def __init__(self):
        self._leases: dict[str, LockLease] = {}
        self._mutex = RLock()

    def acquire(self, name: str, owner: str, ttl_seconds: int) -> bool:
        if not name.strip() or not owner.strip():
            raise ValueError("Kilit adı ve sahibi boş olamaz")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds pozitif olmalıdır")

        now = datetime.now(timezone.utc)
        with self._mutex:
            current = self._leases.get(name)
            if current and current.expires_at > now and current.owner != owner:
                return False
            self._leases[name] = LockLease(
                name=name,
                owner=owner,
                expires_at=now + timedelta(seconds=ttl_seconds),
            )
            return True

    def release(self, name: str, owner: str) -> bool:
        with self._mutex:
            current = self._leases.get(name)
            if current is None or current.owner != owner:
                return False
            del self._leases[name]
            return True
