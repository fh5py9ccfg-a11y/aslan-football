from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class SafeModeDecision:
    enabled: bool
    reason: str
    allowed_actions: tuple[str, ...]

class SafeModeController:
    def evaluate(
        self,
        *,
        circuit_open: bool,
        drift_detected: bool,
        degraded_ratio: float,
    ) -> SafeModeDecision:
        enabled = (
            circuit_open
            or drift_detected
            or degraded_ratio >= 0.50
        )

        if circuit_open:
            reason = "circuit_open"
        elif drift_detected:
            reason = "decision_drift"
        elif degraded_ratio >= 0.50:
            reason = "high_degraded_ratio"
        else:
            reason = "normal_operation"

        actions = (
            ("READ_ONLY", "HISTORICAL_ANALYSIS", "MANUAL_REVIEW")
            if enabled
            else (
                "READ_ONLY",
                "HISTORICAL_ANALYSIS",
                "LIVE_DECISION_SUPPORT",
                "MANUAL_REVIEW",
            )
        )

        return SafeModeDecision(
            enabled=enabled,
            reason=reason,
            allowed_actions=actions,
        )
