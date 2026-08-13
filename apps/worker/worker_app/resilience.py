from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class CircuitState:
    state: str
    failure_count: int
    opened_at: float | None

class CircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 5,
        recovery_timeout_seconds: float = 30.0,
    ):
        if failure_threshold <= 0 or recovery_timeout_seconds <= 0:
            raise ValueError("Circuit breaker değerleri pozitif olmalıdır")
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.failure_count = 0
        self.opened_at = None
        self.state = "CLOSED"

    def before_call(self, now: float | None = None) -> None:
        current = now if now is not None else time.time()
        if self.state == "OPEN":
            if (
                self.opened_at is not None
                and current - self.opened_at >= self.recovery_timeout_seconds
            ):
                self.state = "HALF_OPEN"
                return
            raise RuntimeError("Circuit breaker açık")

    def record_success(self) -> None:
        self.failure_count = 0
        self.opened_at = None
        self.state = "CLOSED"

    def record_failure(self, now: float | None = None) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.opened_at = now if now is not None else time.time()

    def snapshot(self) -> CircuitState:
        return CircuitState(
            state=self.state,
            failure_count=self.failure_count,
            opened_at=self.opened_at,
        )
