from __future__ import annotations
from dataclasses import dataclass

from .consensus import ConsensusReport

@dataclass(frozen=True)
class ReliabilityInput:
    calibration_error: float
    sample_adequacy: float
    data_freshness: float
    consensus: ConsensusReport
    simulation_stability: float

@dataclass(frozen=True)
class ReliabilityReport:
    score: float
    label: str
    warnings: tuple[str, ...]

class PredictionReliabilityEvaluator:
    def evaluate(self, item: ReliabilityInput) -> ReliabilityReport:
        if not 0 <= item.calibration_error <= 1:
            raise ValueError("calibration_error geçersiz")
        for value in (
            item.sample_adequacy,
            item.data_freshness,
            item.simulation_stability,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Güvenilirlik girdisi geçersiz")

        calibration_quality = 1.0 - item.calibration_error
        score = (
            calibration_quality * 0.30
            + item.sample_adequacy * 0.20
            + item.data_freshness * 0.20
            + item.consensus.consensus_score * 0.20
            + item.simulation_stability * 0.10
        )

        warnings = []
        if item.calibration_error > 0.08:
            warnings.append("calibration_error_high")
        if item.sample_adequacy < 0.60:
            warnings.append("sample_size_weak")
        if item.data_freshness < 0.70:
            warnings.append("data_freshness_low")
        if item.consensus.confidence_label == "LOW":
            warnings.append("ensemble_disagreement")
        if item.simulation_stability < 0.70:
            warnings.append("simulation_unstable")

        if score >= 0.82:
            label = "HIGH"
        elif score >= 0.64:
            label = "MEDIUM"
        else:
            label = "LOW"

        return ReliabilityReport(
            score=score,
            label=label,
            warnings=tuple(warnings),
        )
