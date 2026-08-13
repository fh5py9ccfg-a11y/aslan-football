from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass(frozen=True)
class MaintenanceTask:
    name: str
    handler: Callable[[], object]
    critical: bool


@dataclass(frozen=True)
class MaintenanceTaskResult:
    name: str
    passed: bool
    critical: bool
    detail: str


@dataclass(frozen=True)
class MaintenanceRunReport:
    healthy: bool
    results: tuple[MaintenanceTaskResult, ...]


class MaintenanceScheduler:
    def run(self, tasks: list[MaintenanceTask]) -> MaintenanceRunReport:
        if not tasks:
            raise ValueError("En az bir bakım görevi gereklidir")

        results = []
        for task in tasks:
            try:
                value = task.handler()
                passed = bool(value)
                detail = "ok" if passed else "failed"
            except Exception as exc:
                passed = False
                detail = str(exc)

            results.append(
                MaintenanceTaskResult(
                    name=task.name,
                    passed=passed,
                    critical=task.critical,
                    detail=detail,
                )
            )

        healthy = all(
            result.passed or not result.critical
            for result in results
        )
        return MaintenanceRunReport(
            healthy=healthy,
            results=tuple(results),
        )
