from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TypeVar
import time

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    max_attempts: int = 3
    initial_delay_seconds: float = 0.25
    multiplier: float = 2.0
    max_delay_seconds: float = 4.0

    def __post_init__(self) -> None:
        if self.max_attempts <= 0:
            raise ValueError("max_attempts pozitif olmalıdır")
        if self.initial_delay_seconds < 0:
            raise ValueError("initial_delay_seconds negatif olamaz")
        if self.multiplier < 1:
            raise ValueError("multiplier en az 1 olmalıdır")
        if self.max_delay_seconds < self.initial_delay_seconds:
            raise ValueError("max_delay_seconds başlangıç gecikmesinden küçük olamaz")

    def run(
        self,
        operation: Callable[[], T],
        *,
        retryable: tuple[type[BaseException], ...] = (TimeoutError, ConnectionError),
        sleeper: Callable[[float], None] = time.sleep,
    ) -> T:
        delay = self.initial_delay_seconds
        last_error: BaseException | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                return operation()
            except retryable as exc:
                last_error = exc
                if attempt == self.max_attempts:
                    break
                sleeper(delay)
                delay = min(self.max_delay_seconds, delay * self.multiplier)
        assert last_error is not None
        raise last_error
