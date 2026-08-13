from __future__ import annotations
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class SecretAvailability:
    name: str
    available: bool
    source: str

class SecretInspector:
    def inspect_environment(self, name: str) -> SecretAvailability:
        value = os.getenv(name)
        return SecretAvailability(
            name=name,
            available=bool(value and value.strip()),
            source="environment",
        )

    def require(self, name: str) -> str:
        value = os.getenv(name)
        if not value or not value.strip():
            raise RuntimeError(f"Zorunlu secret tanımlı değil: {name}")
        return value.strip()
