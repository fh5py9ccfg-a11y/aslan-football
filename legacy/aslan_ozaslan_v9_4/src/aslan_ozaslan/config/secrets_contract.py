from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


class SecretProvider(Protocol):
    def get(self, name: str) -> str | None:
        ...


@dataclass(frozen=True)
class RequiredSecret:
    name: str
    minimum_length: int = 1


class SecretResolver:
    def __init__(self, provider: SecretProvider):
        self.provider = provider

    def require(self, requirements: list[RequiredSecret]) -> dict[str, str]:
        resolved = {}
        missing = []
        for requirement in requirements:
            value = self.provider.get(requirement.name)
            if value is None or len(value) < requirement.minimum_length:
                missing.append(requirement.name)
                continue
            resolved[requirement.name] = value
        if missing:
            raise ValueError("Eksik veya zayıf sırlar: " + ",".join(sorted(missing)))
        return resolved
