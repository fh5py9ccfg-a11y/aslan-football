from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RollbackPlan:
    from_version: str
    to_version: str
    steps: tuple[str, ...]


class RollbackPlanner:
    def build(self, from_version: str, to_version: str) -> RollbackPlan:
        if not from_version.strip() or not to_version.strip():
            raise ValueError("Sürüm bilgileri boş olamaz")
        if from_version == to_version:
            raise ValueError("Aynı sürüme rollback yapılamaz")

        return RollbackPlan(
            from_version=from_version,
            to_version=to_version,
            steps=(
                "freeze-new-deployments",
                "switch-application-version",
                "verify-database-compatibility",
                "run-smoke-tests",
                "restore-traffic",
                "monitor-errors",
            ),
        )
