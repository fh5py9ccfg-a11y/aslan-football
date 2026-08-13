from __future__ import annotations
from datetime import datetime, timedelta, timezone

class RetryPolicy:
    def __init__(
        self,
        *,
        max_attempts: int = 5,
        base_delay_seconds: int = 5,
        max_delay_seconds: int = 300,
    ):
        if min(max_attempts, base_delay_seconds, max_delay_seconds) <= 0:
            raise ValueError("Retry değerleri pozitif olmalıdır")
        self.max_attempts = max_attempts
        self.base_delay_seconds = base_delay_seconds
        self.max_delay_seconds = max_delay_seconds

    def next_delay(self, attempt_count: int) -> int:
        if attempt_count < 0:
            raise ValueError("attempt_count negatif olamaz")
        return min(
            self.max_delay_seconds,
            self.base_delay_seconds * (2 ** attempt_count),
        )

    def next_available_at(self, attempt_count: int) -> str:
        delay = self.next_delay(attempt_count)
        return (
            datetime.now(timezone.utc)
            + timedelta(seconds=delay)
        ).isoformat()
