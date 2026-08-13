from __future__ import annotations
from dataclasses import dataclass
from statistics import mean

from .domain import DecisionQualitySample

@dataclass(frozen=True)
class DecisionDriftReport:
    detected: bool
    confidence_shift: float
    risk_shift: float
    latency_shift_ms: float
    reasons: tuple[str, ...]

class DecisionDriftDetector:
    def detect(
        self,
        baseline: tuple[DecisionQualitySample, ...],
        recent: tuple[DecisionQualitySample, ...],
        *,
        confidence_threshold: float = 0.12,
        risk_threshold: float = 0.15,
        latency_threshold_ms: float = 30.0,
    ) -> DecisionDriftReport:
        if not baseline or not recent:
            raise ValueError("Baseline ve recent örnekleri gereklidir")

        baseline_conf = mean(item.confidence for item in baseline)
        recent_conf = mean(item.confidence for item in recent)
        baseline_risk = mean(item.risk_score for item in baseline)
        recent_risk = mean(item.risk_score for item in recent)
        baseline_latency = mean(item.latency_ms for item in baseline)
        recent_latency = mean(item.latency_ms for item in recent)

        confidence_shift = recent_conf - baseline_conf
        risk_shift = recent_risk - baseline_risk
        latency_shift = recent_latency - baseline_latency

        reasons = []
        if confidence_shift <= -abs(confidence_threshold):
            reasons.append("confidence_drop")
        if risk_shift >= abs(risk_threshold):
            reasons.append("risk_increase")
        if latency_shift >= abs(latency_threshold_ms):
            reasons.append("latency_regression")

        return DecisionDriftReport(
            detected=bool(reasons),
            confidence_shift=confidence_shift,
            risk_shift=risk_shift,
            latency_shift_ms=latency_shift,
            reasons=tuple(reasons),
        )
