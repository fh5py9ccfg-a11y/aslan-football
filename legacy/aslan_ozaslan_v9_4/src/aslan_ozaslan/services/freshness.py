from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

@dataclass(frozen=True)
class FreshnessResult:
    accepted: bool
    age_minutes: int
    reason: str

class FreshnessPolicy:
    def __init__(self, max_age_minutes: int = 180):
        if max_age_minutes <= 0:
            raise ValueError("max_age_minutes pozitif olmalıdır")
        self.max_age_minutes = max_age_minutes

    def evaluate(self, observed_at: datetime, now: datetime | None = None):
        current = now or datetime.now(timezone.utc)
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
        age = current - observed_at
        age_minutes = max(0, int(age.total_seconds() // 60))
        if age > timedelta(minutes=self.max_age_minutes):
            return FreshnessResult(False, age_minutes, "Veri güncellik eşiğini aştı.")
        return FreshnessResult(True, age_minutes, "Veri güncel.")
