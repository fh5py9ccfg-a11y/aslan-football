from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class RetryDecision:
    should_retry: bool
    attempt: int
    delay_seconds: float
    exhausted: bool

class ExponentialRetryPolicy:
    def __init__(
        self,
        *,
        max_attempts: int = 5,
        base_delay_seconds: float = 1.0,
        max_delay_seconds: float = 60.0,
    ):
        if max_attempts <= 0:
            raise ValueError("max_attempts pozitif olmalıdır")
        if base_delay_seconds <= 0 or max_delay_seconds <= 0:
            raise ValueError("Gecikme değerleri pozitif olmalıdır")
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds

    def decide(self, current_attempt: int) -> RetryDecision:
        if current_attempt < 0:
            raise ValueError("current_attempt negatif olamaz")

        next_attempt = current_attempt + 1
        exhausted = next_attempt >= self.max_attempts
        if exhausted:
            return RetryDecision(
                should_retry=False,
                attempt=next_attempt,
                delay_seconds=0.0,
                exhausted=True,
            )

        delay = min(
            self.max_delay_seconds,
            self.base_delay_seconds * (2 ** current_attempt),
        )
        return RetryDecision(
            should_retry=True,
            attempt=next_attempt,
            delay_seconds=delay,
            exhausted=False,
        )
