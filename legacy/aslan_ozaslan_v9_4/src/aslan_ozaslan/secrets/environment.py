from __future__ import annotations
import os

class EnvironmentSecretProvider:
    def get_required(self, name: str) -> str:
        value = os.getenv(name)
        if value is None or not value.strip():
            raise RuntimeError(f"Gerekli gizli değer tanımlı değil: {name}")
        return value.strip()

    def get_optional(self, name: str) -> str | None:
        value = os.getenv(name)
        return value.strip() if value and value.strip() else None
