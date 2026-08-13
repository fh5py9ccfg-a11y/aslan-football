from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class InjuryRiskReport:
    risk_score: float
    label: str

class InjuryRiskModel:
    def evaluate(
        self,
        *,
        injury_days_last_365: int,
        minutes_last_365: int,
    ) -> InjuryRiskReport:
        if injury_days_last_365 < 0 or minutes_last_365 < 0:
            raise ValueError("Sakatlık girdileri negatif olamaz")

        injury_ratio = min(injury_days_last_365 / 180.0, 1.0)
        availability_penalty = (
            max(0.0, 1.0 - minutes_last_365 / 2700.0)
        )
        risk = min(
            injury_ratio * 0.70
            + availability_penalty * 0.30,
            1.0,
        )

        if risk >= 0.70:
            label = "HIGH"
        elif risk >= 0.40:
            label = "MEDIUM"
        else:
            label = "LOW"

        return InjuryRiskReport(risk, label)
