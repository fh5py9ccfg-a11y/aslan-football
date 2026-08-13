from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CanaryMetrics:
    request_count: int
    error_rate: float
    p95_latency_ms: float


@dataclass(frozen=True)
class CanaryDecision:
    promote: bool
    reasons: tuple[str, ...]


class CanaryEvaluator:
    def __init__(
        self,
        *,
        minimum_requests: int = 100,
        maximum_error_rate: float = 0.02,
        maximum_p95_latency_ms: float = 1000.0,
    ):
        if minimum_requests <= 0:
            raise ValueError("minimum_requests pozitif olmalıdır")
        if not 0 <= maximum_error_rate <= 1:
            raise ValueError("maximum_error_rate 0 ile 1 arasında olmalıdır")
        if maximum_p95_latency_ms <= 0:
            raise ValueError("maximum_p95_latency_ms pozitif olmalıdır")

        self.minimum_requests = minimum_requests
        self.maximum_error_rate = maximum_error_rate
        self.maximum_p95_latency_ms = maximum_p95_latency_ms

    def evaluate(self, metrics: CanaryMetrics) -> CanaryDecision:
        reasons = []

        if metrics.request_count < self.minimum_requests:
            reasons.append("insufficient_requests")
        if not 0 <= metrics.error_rate <= 1:
            reasons.append("invalid_error_rate")
        elif metrics.error_rate > self.maximum_error_rate:
            reasons.append("error_rate_too_high")
        if metrics.p95_latency_ms > self.maximum_p95_latency_ms:
            reasons.append("latency_too_high")

        return CanaryDecision(
            promote=not reasons,
            reasons=tuple(reasons),
        )
