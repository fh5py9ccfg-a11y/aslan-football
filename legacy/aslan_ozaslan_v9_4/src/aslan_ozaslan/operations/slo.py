from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ServiceLevelObjective:
    name: str
    target: float
    window_days: int


@dataclass(frozen=True)
class SLOEvaluation:
    name: str
    achieved: float
    target: float
    met: bool
    error_budget_remaining: float


class SLOEvaluator:
    def evaluate(self, slo: ServiceLevelObjective, achieved: float) -> SLOEvaluation:
        if not 0 < slo.target <= 1:
            raise ValueError("SLO target 0 ile 1 arasında olmalıdır")
        if slo.window_days <= 0:
            raise ValueError("SLO window pozitif olmalıdır")
        if not 0 <= achieved <= 1:
            raise ValueError("achieved 0 ile 1 arasında olmalıdır")

        allowed_failure = 1 - slo.target
        actual_failure = 1 - achieved
        remaining = max(0.0, allowed_failure - actual_failure)

        return SLOEvaluation(
            name=slo.name,
            achieved=achieved,
            target=slo.target,
            met=achieved >= slo.target,
            error_budget_remaining=round(remaining, 6),
        )
