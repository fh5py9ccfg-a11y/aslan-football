from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class CostEfficiencyReport:
    score: float
    annual_cost: float
    cost_per_value_point: float

class TransferEconomicsModel:
    def evaluate(
        self,
        *,
        value_score: float,
        annual_salary: float,
        estimated_fee: float,
        amortization_years: float = 4.0,
    ) -> CostEfficiencyReport:
        if value_score <= 0:
            raise ValueError("value_score pozitif olmalıdır")
        if min(annual_salary, estimated_fee, amortization_years) < 0:
            raise ValueError("Ekonomik girdiler negatif olamaz")
        if amortization_years == 0:
            raise ValueError("amortization_years sıfır olamaz")

        annual_cost = annual_salary + estimated_fee / amortization_years
        cost_per_point = annual_cost / value_score
        score = 1.0 / (1.0 + cost_per_point / 1_000_000.0)

        return CostEfficiencyReport(
            score=max(0.0, min(score, 1.0)),
            annual_cost=annual_cost,
            cost_per_value_point=cost_per_point,
        )

    def contract_leverage(
        self,
        *,
        contract_months_remaining: int,
    ) -> float:
        if contract_months_remaining < 0:
            raise ValueError("contract_months_remaining negatif olamaz")
        if contract_months_remaining <= 6:
            return 1.0
        if contract_months_remaining <= 12:
            return 0.85
        if contract_months_remaining <= 24:
            return 0.60
        if contract_months_remaining <= 36:
            return 0.40
        return 0.20
