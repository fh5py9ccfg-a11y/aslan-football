from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ClubBudget:
    transfer_budget: float
    salary_budget: float
    current_salary: float

    def validate(self) -> None:
        if min(
            self.transfer_budget,
            self.salary_budget,
            self.current_salary,
        ) < 0:
            raise ValueError("Bütçe değerleri negatif olamaz")

@dataclass(frozen=True)
class BudgetAssessment:
    salary_utilization: float
    salary_headroom: float
    transfer_headroom: float
    status: str

class ClubBudgetAnalyzer:
    def evaluate(self, budget: ClubBudget) -> BudgetAssessment:
        budget.validate()

        utilization = (
            budget.current_salary / budget.salary_budget
            if budget.salary_budget else 1.0
        )
        salary_headroom = max(
            0.0,
            budget.salary_budget - budget.current_salary,
        )

        if utilization >= 0.95:
            status = "CRITICAL"
        elif utilization >= 0.85:
            status = "TIGHT"
        else:
            status = "HEALTHY"

        return BudgetAssessment(
            salary_utilization=utilization,
            salary_headroom=salary_headroom,
            transfer_headroom=budget.transfer_budget,
            status=status,
        )
