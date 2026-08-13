from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Runbook:
    incident_code: str
    title: str
    steps: tuple[str, ...]


class RunbookRegistry:
    def __init__(self):
        self._items: dict[str, Runbook] = {}

    def register(self, runbook: Runbook) -> None:
        if not runbook.incident_code.strip():
            raise ValueError("Incident kodu boş olamaz")
        if len(runbook.steps) < 2:
            raise ValueError("Runbook en az iki adım içermelidir")
        self._items[runbook.incident_code] = runbook

    def get(self, incident_code: str) -> Runbook:
        try:
            return self._items[incident_code]
        except KeyError as exc:
            raise KeyError(f"Runbook bulunamadı: {incident_code}") from exc
