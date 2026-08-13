from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class CircuitState:
    open: bool
    failure_count: int
    reason: str | None

class DecisionCircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        degraded_ratio_threshold: float = 0.40,
    ):
        if failure_threshold <= 0:
            raise ValueError("failure_threshold pozitif olmalıdır")
        if not 0 < degraded_ratio_threshold <= 1:
            raise ValueError("degraded_ratio_threshold geçersiz")
        self.failure_threshold = failure_threshold
        self.degraded_ratio_threshold = degraded_ratio_threshold
        self.failure_count = 0
        self._open = False
        self._reason = None

    def observe(
        self,
        *,
        drift_detected: bool,
        degraded_ratio: float,
    ) -> CircuitState:
        failure = drift_detected or degraded_ratio >= self.degraded_ratio_threshold

        if failure:
            self.failure_count += 1
        else:
            self.failure_count = 0

        if self.failure_count >= self.failure_threshold:
            self._open = True
            self._reason = (
                "decision_quality_unstable"
                if drift_detected
                else "latency_degradation"
            )

        return CircuitState(
            open=self._open,
            failure_count=self.failure_count,
            reason=self._reason,
        )

    def reset(self) -> CircuitState:
        self.failure_count = 0
        self._open = False
        self._reason = None
        return CircuitState(False, 0, None)
