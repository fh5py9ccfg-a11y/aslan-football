from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone


@dataclass(frozen=True)
class SecretRotationPolicy:
    name: str
    rotate_every_days: int
    overlap_hours: int


@dataclass(frozen=True)
class SecretRotationDecision:
    due: bool
    rotate_at: str
    retire_previous_at: str


class SecretRotationPlanner:
    def plan(
        self,
        policy: SecretRotationPolicy,
        *,
        last_rotated_at: datetime,
        now: datetime | None = None,
    ) -> SecretRotationDecision:
        if policy.rotate_every_days <= 0:
            raise ValueError("rotate_every_days pozitif olmalıdır")
        if policy.overlap_hours < 0:
            raise ValueError("overlap_hours negatif olamaz")
        if last_rotated_at.tzinfo is None:
            raise ValueError("last_rotated_at timezone içermelidir")

        moment = now or datetime.now(timezone.utc)
        rotate_at = last_rotated_at + timedelta(days=policy.rotate_every_days)
        retire_at = rotate_at + timedelta(hours=policy.overlap_hours)
        return SecretRotationDecision(
            due=moment >= rotate_at,
            rotate_at=rotate_at.isoformat(),
            retire_previous_at=retire_at.isoformat(),
        )
