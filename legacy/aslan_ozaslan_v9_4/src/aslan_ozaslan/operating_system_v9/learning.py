from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DecisionOutcome:
    decision_id: str
    expert: str
    predicted_success: float
    realized_success: float

    def validate(self) -> None:
        if not self.decision_id.strip() or not self.expert.strip():
            raise ValueError("Karar alanları boş olamaz")
        for value in (
            self.predicted_success,
            self.realized_success,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Başarı skorları geçersiz")

@dataclass(frozen=True)
class ExpertPerformance:
    expert: str
    sample_count: int
    calibration_error: float
    mean_realized_success: float
    suggested_weight: float

class ContinuousLearningEvaluator:
    def evaluate(
        self,
        outcomes: tuple[DecisionOutcome, ...],
    ) -> tuple[ExpertPerformance, ...]:
        if not outcomes:
            raise ValueError("Outcome verisi gerekir")

        grouped = {}
        for outcome in outcomes:
            outcome.validate()
            grouped.setdefault(outcome.expert, []).append(outcome)

        reports = []
        for expert, items in sorted(grouped.items()):
            error = sum(
                abs(item.predicted_success - item.realized_success)
                for item in items
            ) / len(items)
            realized = sum(
                item.realized_success for item in items
            ) / len(items)
            suggested_weight = max(
                0.25,
                min(1.50, (1.0 - error) * (0.75 + realized * 0.75)),
            )
            reports.append(
                ExpertPerformance(
                    expert=expert,
                    sample_count=len(items),
                    calibration_error=error,
                    mean_realized_success=realized,
                    suggested_weight=suggested_weight,
                )
            )
        return tuple(reports)
