from __future__ import annotations
from dataclasses import dataclass

from .domain import StreamCheckpoint

@dataclass(frozen=True)
class RecoveryPlan:
    stream_id: str
    resume_from_sequence: int
    replay_required: bool
    reason: str

class StreamRecoveryPlanner:
    def build(
        self,
        *,
        checkpoint: StreamCheckpoint,
        provider_high_watermark: int,
    ) -> RecoveryPlan:
        if provider_high_watermark < -1:
            raise ValueError("provider_high_watermark geçersiz")

        resume = checkpoint.last_sequence + 1
        replay_required = provider_high_watermark >= resume
        reason = (
            "provider_has_unprocessed_events"
            if replay_required
            else "stream_is_current"
        )
        return RecoveryPlan(
            stream_id=checkpoint.stream_id,
            resume_from_sequence=resume,
            replay_required=replay_required,
            reason=reason,
        )
