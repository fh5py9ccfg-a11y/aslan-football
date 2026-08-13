from __future__ import annotations
from dataclasses import dataclass

from aslan_ozaslan.validation_v5 import BaselineComparison, CalibrationReport, LeakageReport

@dataclass(frozen=True)
class ModelPromotionPolicy:
    minimum_brier_improvement: float
    maximum_calibration_error: float
    minimum_samples: int

@dataclass(frozen=True)
class ModelPromotionDecision:
    allowed: bool
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]

class FootballModelPromotionGate:
    def evaluate(
        self,
        *,
        policy: ModelPromotionPolicy,
        comparison: BaselineComparison,
        calibration: CalibrationReport,
        leakage: LeakageReport,
        samples: int,
    ) -> ModelPromotionDecision:
        blockers = []
        warnings = []

        if not leakage.safe:
            blockers.append("data_leakage_detected")
        if samples < policy.minimum_samples:
            blockers.append("insufficient_samples")
        if comparison.brier_improvement < policy.minimum_brier_improvement:
            blockers.append("insufficient_brier_improvement")
        if calibration.expected_calibration_error > policy.maximum_calibration_error:
            blockers.append("calibration_error_too_high")
        if comparison.accuracy_improvement < 0:
            warnings.append("accuracy_regression")
        if not comparison.candidate_better:
            blockers.append("candidate_not_better_than_baseline")

        return ModelPromotionDecision(
            allowed=not blockers,
            blockers=tuple(blockers),
            warnings=tuple(warnings),
        )
