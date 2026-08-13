from __future__ import annotations
from dataclasses import dataclass
from statistics import mean

from .domain import MonitoringSnapshot
from .drift import DecisionDriftDetector
from .safe_mode import SafeModeController

class DecisionMonitoringAggregator:
    def __init__(
        self,
        *,
        circuit_breaker,
        drift_detector: DecisionDriftDetector | None = None,
        safe_mode_controller: SafeModeController | None = None,
    ):
        self.circuit_breaker = circuit_breaker
        self.drift_detector = drift_detector or DecisionDriftDetector()
        self.safe_mode_controller = (
            safe_mode_controller or SafeModeController()
        )

    def build(
        self,
        *,
        baseline,
        recent,
    ) -> tuple[MonitoringSnapshot, object, object]:
        if not recent:
            raise ValueError("Recent örnek gereklidir")

        drift = self.drift_detector.detect(baseline, recent)

        latencies = sorted(item.latency_ms for item in recent)
        index = min(
            len(latencies) - 1,
            max(0, int(round((len(latencies) - 1) * 0.95))),
        )
        p95 = latencies[index]
        degraded_ratio = (
            sum(1 for item in recent if item.degraded) / len(recent)
        )

        circuit = self.circuit_breaker.observe(
            drift_detected=drift.detected,
            degraded_ratio=degraded_ratio,
        )
        safe_mode = self.safe_mode_controller.evaluate(
            circuit_open=circuit.open,
            drift_detected=drift.detected,
            degraded_ratio=degraded_ratio,
        )

        snapshot = MonitoringSnapshot(
            samples=len(recent),
            average_confidence=mean(
                item.confidence for item in recent
            ),
            average_risk=mean(item.risk_score for item in recent),
            p95_latency_ms=p95,
            degraded_ratio=degraded_ratio,
            drift_detected=drift.detected,
            circuit_open=circuit.open,
            safe_mode=safe_mode.enabled,
        )
        return snapshot, drift, safe_mode
