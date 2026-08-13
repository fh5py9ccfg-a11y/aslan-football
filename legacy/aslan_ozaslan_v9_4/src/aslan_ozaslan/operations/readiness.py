from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ReadinessItem:
    name: str
    passed: bool
    critical: bool
    detail: str


@dataclass(frozen=True)
class ProductionReadinessReport:
    ready: bool
    score: int
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    items: tuple[ReadinessItem, ...]


class ProductionReadinessEvaluator:
    def evaluate(self, items: list[ReadinessItem]) -> ProductionReadinessReport:
        if not items:
            raise ValueError("Hazırlık raporu için kontrol gereklidir")

        blockers = tuple(
            item.name for item in items
            if item.critical and not item.passed
        )
        warnings = tuple(
            item.name for item in items
            if not item.critical and not item.passed
        )
        passed_weight = sum(2 if item.critical else 1 for item in items if item.passed)
        total_weight = sum(2 if item.critical else 1 for item in items)
        score = round((passed_weight / total_weight) * 100)

        return ProductionReadinessReport(
            ready=not blockers,
            score=score,
            blockers=blockers,
            warnings=warnings,
            items=tuple(items),
        )
