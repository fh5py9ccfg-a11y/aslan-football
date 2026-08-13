from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CacheNamespace:
    name: str
    version: int = 1

    def key(self, raw_key: str) -> str:
        if not self.name.strip() or not raw_key.strip():
            raise ValueError("Namespace ve anahtar boş olamaz")
        return f"{self.name}:v{self.version}:{raw_key}"


class NamespacedCache:
    def __init__(self, adapter, namespace: CacheNamespace):
        self.adapter = adapter
        self.namespace = namespace

    def get(self, raw_key: str) -> Any | None:
        return self.adapter.get(self.namespace.key(raw_key))

    def set(self, raw_key: str, value: Any, ttl_seconds: int) -> None:
        self.adapter.set(self.namespace.key(raw_key), value, ttl_seconds)

    def delete(self, raw_key: str) -> None:
        self.adapter.delete(self.namespace.key(raw_key))
