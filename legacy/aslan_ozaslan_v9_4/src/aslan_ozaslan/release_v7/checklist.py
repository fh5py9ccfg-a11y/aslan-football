from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ReleaseChecklistItem:
    name: str
    completed: bool
    required: bool

class ReleaseChecklist:
    def evaluate(self, items: tuple[ReleaseChecklistItem, ...]) -> tuple[str, ...]:
        return tuple(
            item.name
            for item in items
            if item.required and not item.completed
        )
