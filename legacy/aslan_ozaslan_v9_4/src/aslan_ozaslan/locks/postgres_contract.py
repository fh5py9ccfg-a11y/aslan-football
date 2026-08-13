from __future__ import annotations

from dataclasses import dataclass
import hashlib


@dataclass(frozen=True)
class PostgresAdvisoryLockKey:
    namespace: int
    resource: int


def advisory_lock_key(name: str) -> PostgresAdvisoryLockKey:
    if not name.strip():
        raise ValueError("Kilit adı boş olamaz")
    digest = hashlib.sha256(name.encode("utf-8")).digest()
    namespace = int.from_bytes(digest[:4], "big", signed=False)
    resource = int.from_bytes(digest[4:8], "big", signed=False)
    return PostgresAdvisoryLockKey(namespace, resource)


def acquire_sql() -> str:
    return "SELECT pg_try_advisory_lock(%s, %s)"


def release_sql() -> str:
    return "SELECT pg_advisory_unlock(%s, %s)"
