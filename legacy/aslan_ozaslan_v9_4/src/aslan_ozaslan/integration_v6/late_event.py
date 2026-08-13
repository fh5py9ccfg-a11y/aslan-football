from __future__ import annotations
from dataclasses import dataclass

from .provider_events import ProviderEventRecord

@dataclass(frozen=True)
class LateEventDecision:
    accepted: bool
    late: bool
    requires_replay: bool
    reason: str

class LateEventPolicy:
    def __init__(self, allowed_lateness_minutes: int = 5):
        if allowed_lateness_minutes < 0:
            raise ValueError("allowed_lateness_minutes negatif olamaz")
        self.allowed_lateness_minutes = allowed_lateness_minutes

    def evaluate(
        self,
        event: ProviderEventRecord,
        *,
        current_minute: int,
    ) -> LateEventDecision:
        event.validate()
        lateness = current_minute - event.minute

        if lateness <= 0:
            return LateEventDecision(True, False, False, "on_time")

        if lateness <= self.allowed_lateness_minutes:
            return LateEventDecision(True, True, False, "late_but_acceptable")

        return LateEventDecision(True, True, True, "late_requires_replay")
