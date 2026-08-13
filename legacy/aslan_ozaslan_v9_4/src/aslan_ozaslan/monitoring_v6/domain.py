from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DecisionQualitySample:
    fixture_id: str
    minute: int
    confidence: float
    risk_score: float
    opportunity_score: float
    latency_ms: float
    degraded: bool

    def validate(self) -> None:
        if not self.fixture_id.strip():
            raise ValueError("fixture_id boş olamaz")
        if not 0 <= self.minute <= 130:
            raise ValueError("minute geçersiz")
        for value in (
            self.confidence,
            self.risk_score,
            self.opportunity_score,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Kalite skoru 0 ile 1 arasında olmalıdır")
        if self.latency_ms < 0:
            raise ValueError("latency_ms negatif olamaz")

@dataclass(frozen=True)
class MonitoringSnapshot:
    samples: int
    average_confidence: float
    average_risk: float
    p95_latency_ms: float
    degraded_ratio: float
    drift_detected: bool
    circuit_open: bool
    safe_mode: bool
