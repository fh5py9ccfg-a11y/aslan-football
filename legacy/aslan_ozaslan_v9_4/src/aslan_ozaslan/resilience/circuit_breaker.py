from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from time import monotonic


class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class CircuitBreaker:
    failure_threshold: int = 3
    recovery_timeout_seconds: float = 60.0

    def __post_init__(self):
        if self.failure_threshold <= 0:
            raise ValueError("failure_threshold pozitif olmalıdır")
        if self.recovery_timeout_seconds <= 0:
            raise ValueError("recovery_timeout_seconds pozitif olmalıdır")
        self._failure_count = 0
        self._opened_at: float | None = None
        self._state = CircuitState.CLOSED

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN and self._opened_at is not None:
            if monotonic() - self._opened_at >= self.recovery_timeout_seconds:
                self._state = CircuitState.HALF_OPEN
        return self._state

    def allow_request(self) -> bool:
        return self.state in (CircuitState.CLOSED, CircuitState.HALF_OPEN)

    def record_success(self) -> None:
        self._failure_count = 0
        self._opened_at = None
        self._state = CircuitState.CLOSED

    def record_failure(self) -> None:
        self._failure_count += 1
        if self._failure_count >= self.failure_threshold:
            self._state = CircuitState.OPEN
            self._opened_at = monotonic()
