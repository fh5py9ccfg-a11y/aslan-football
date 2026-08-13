from __future__ import annotations
from dataclasses import dataclass

from .domain import SeasonObjective

@dataclass(frozen=True)
class ObjectiveProgress:
    name: str
    progress: float
    achieved: bool
    weighted_score: float

class SeasonObjectiveTracker:
    def evaluate(
        self,
        objectives: tuple[SeasonObjective, ...],
    ) -> tuple[ObjectiveProgress, ...]:
        if not objectives:
            raise ValueError("En az bir sezon hedefi gerekir")

        reports = []
        for objective in objectives:
            objective.validate()

            if objective.target_value == 0:
                progress = 1.0 if objective.current_value == 0 else 0.0
            elif objective.higher_is_better:
                progress = objective.current_value / objective.target_value
            else:
                progress = objective.target_value / max(
                    objective.current_value,
                    1e-9,
                )

            progress = max(0.0, min(progress, 1.25))
            reports.append(
                ObjectiveProgress(
                    name=objective.name,
                    progress=progress,
                    achieved=progress >= 1.0,
                    weighted_score=progress * objective.weight,
                )
            )

        return tuple(reports)

    def aggregate(
        self,
        reports: tuple[ObjectiveProgress, ...],
        objectives: tuple[SeasonObjective, ...],
    ) -> float:
        total_weight = sum(item.weight for item in objectives)
        if total_weight <= 0:
            raise ValueError("Toplam hedef ağırlığı pozitif olmalıdır")
        return min(
            1.0,
            sum(report.weighted_score for report in reports)
            / total_weight,
        )
