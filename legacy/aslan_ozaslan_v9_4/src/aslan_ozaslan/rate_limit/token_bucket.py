from __future__ import annotations
from dataclasses import dataclass, field
from time import monotonic

@dataclass
class TokenBucket:
    capacity: int
    refill_rate_per_second: float
    tokens: float = field(init=False)
    updated_at: float = field(init=False)

    def __post_init__(self):
        if self.capacity <= 0:
            raise ValueError("capacity pozitif olmalıdır")
        if self.refill_rate_per_second <= 0:
            raise ValueError("refill_rate_per_second pozitif olmalıdır")
        self.tokens = float(self.capacity)
        self.updated_at = monotonic()

    def allow(self, cost: float = 1.0) -> bool:
        if cost <= 0:
            raise ValueError("cost pozitif olmalıdır")
        now = monotonic()
        elapsed = now - self.updated_at
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate_per_second)
        self.updated_at = now
        if self.tokens >= cost:
            self.tokens -= cost
            return True
        return False
