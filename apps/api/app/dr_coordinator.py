from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass(frozen=True)
class RecoveryObjective:
    rpo_seconds: int
    estimated_rto_seconds: int
    healthy: bool
    reason: str

class DisasterRecoveryCoordinator:
    def __init__(
        self,
        *,
        repository,
        max_rto_seconds: int = 300,
    ):
        if max_rto_seconds <= 0:
            raise ValueError("max_rto_seconds pozitif olmalıdır")
        self.repository = repository
        self.max_rto_seconds = max_rto_seconds

    def evaluate(
        self,
        region: str,
        *,
        now: int | None = None,
    ) -> RecoveryObjective:
        current = int(now if now is not None else time.time())
        checkpoint = self.repository.get_checkpoint(region)
        if checkpoint is None:
            return RecoveryObjective(
                rpo_seconds=0,
                estimated_rto_seconds=self.max_rto_seconds,
                healthy=False,
                reason="Checkpoint bulunamadı",
            )

        staleness = max(0, current - checkpoint.updated_at)
        estimated_rto = min(
            self.max_rto_seconds,
            30 + staleness,
        )
        healthy = (
            checkpoint.rpo_seconds
            <= self.repository.max_rpo_seconds
            and estimated_rto <= self.max_rto_seconds
        )
        return RecoveryObjective(
            rpo_seconds=checkpoint.rpo_seconds,
            estimated_rto_seconds=estimated_rto,
            healthy=healthy,
            reason=(
                "Recovery hedefleri karşılanıyor"
                if healthy
                else "Recovery hedefleri karşılanmıyor"
            ),
        )
