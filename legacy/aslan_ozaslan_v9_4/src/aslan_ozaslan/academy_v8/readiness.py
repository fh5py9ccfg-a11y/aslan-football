from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class FirstTeamReadinessReport:
    score: float
    label: str
    blockers: tuple[str, ...]

class FirstTeamReadinessEvaluator:
    def evaluate(
        self,
        *,
        current_level: float,
        physical_readiness: float,
        tactical_readiness: float,
        psychological_readiness: float,
        injury_risk: float,
    ) -> FirstTeamReadinessReport:
        for value in (
            current_level,
            physical_readiness,
            tactical_readiness,
            psychological_readiness,
            injury_risk,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Hazırlık girdileri geçersiz")

        score = (
            current_level * 0.30
            + physical_readiness * 0.24
            + tactical_readiness * 0.22
            + psychological_readiness * 0.16
            + (1.0 - injury_risk) * 0.08
        )

        blockers = []
        if physical_readiness < 0.60:
            blockers.append("physical_readiness_low")
        if tactical_readiness < 0.60:
            blockers.append("tactical_readiness_low")
        if psychological_readiness < 0.55:
            blockers.append("psychological_readiness_low")
        if injury_risk >= 0.60:
            blockers.append("injury_risk_high")

        if score >= 0.78 and not blockers:
            label = "READY"
        elif score >= 0.65:
            label = "NEAR_READY"
        else:
            label = "NOT_READY"

        return FirstTeamReadinessReport(
            score=score,
            label=label,
            blockers=tuple(blockers),
        )
