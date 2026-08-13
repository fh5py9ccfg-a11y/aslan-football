from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class CacheHealth:
    status: str
    last_success_at: float | None
    last_error: str | None
    expires_at: float
    stale_until: float

class MetadataCircuitBreaker:
    def __init__(
        self,
        *,
        failure_threshold: int = 3,
        recovery_timeout_seconds: float = 30.0,
    ):
        if failure_threshold <= 0 or recovery_timeout_seconds <= 0:
            raise ValueError("Circuit breaker değerleri pozitif olmalıdır")
        self.failure_threshold = failure_threshold
        self.recovery_timeout_seconds = recovery_timeout_seconds
        self.failure_count = 0
        self.opened_at: float | None = None
        self.state = "CLOSED"

    def allow(self, *, now: float | None = None) -> bool:
        current = now if now is not None else time.time()
        if self.state != "OPEN":
            return True
        if (
            self.opened_at is not None
            and current - self.opened_at >= self.recovery_timeout_seconds
        ):
            self.state = "HALF_OPEN"
            return True
        return False

    def success(self) -> None:
        self.failure_count = 0
        self.opened_at = None
        self.state = "CLOSED"

    def failure(self, *, now: float | None = None) -> None:
        self.failure_count += 1
        if self.failure_count >= self.failure_threshold:
            self.state = "OPEN"
            self.opened_at = now if now is not None else time.time()
