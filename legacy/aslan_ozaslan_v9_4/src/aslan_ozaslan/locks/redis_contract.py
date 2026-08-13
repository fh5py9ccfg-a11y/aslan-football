from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class RedisClientProtocol(Protocol):
    def set(self, key: str, value: str, *, nx: bool, ex: int) -> bool: ...
    def get(self, key: str) -> str | None: ...
    def delete(self, key: str) -> int: ...


@dataclass
class RedisDistributedLock:
    client: RedisClientProtocol
    prefix: str = "aslan-lock"

    def acquire(self, name: str, owner: str, ttl_seconds: int) -> bool:
        if not name.strip() or not owner.strip():
            raise ValueError("Kilit adı ve sahibi boş olamaz")
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds pozitif olmalıdır")
        return bool(
            self.client.set(
                f"{self.prefix}:{name}",
                owner,
                nx=True,
                ex=ttl_seconds,
            )
        )

    def release(self, name: str, owner: str) -> bool:
        key = f"{self.prefix}:{name}"
        if self.client.get(key) != owner:
            return False
        return self.client.delete(key) == 1
