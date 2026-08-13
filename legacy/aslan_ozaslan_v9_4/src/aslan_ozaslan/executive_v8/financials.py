from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutiveFinancialReport:
    wage_to_revenue_ratio: float
    transfer_balance_ratio: float
    liquidity_score: float
    stability_score: float
    status: str

class ExecutiveFinancialAnalyzer:
    def evaluate(
        self,
        *,
        revenue: float,
        wage_cost: float,
        transfer_balance: float,
        cash_reserve: float,
        annual_commitments: float,
    ) -> ExecutiveFinancialReport:
        if min(revenue, wage_cost, cash_reserve, annual_commitments) < 0:
            raise ValueError("Finansal girdiler negatif olamaz")

        wage_ratio = wage_cost / revenue if revenue else 1.0
        transfer_ratio = transfer_balance / revenue if revenue else 0.0
        liquidity = (
            cash_reserve / annual_commitments
            if annual_commitments
            else 1.0
        )
        liquidity_score = max(0.0, min(liquidity, 1.0))

        wage_component = max(0.0, 1.0 - max(0.0, wage_ratio - 0.55) / 0.35)
        transfer_component = max(
            0.0,
            min(1.0, 0.55 + transfer_ratio * 0.80),
        )
        stability = (
            wage_component * 0.45
            + transfer_component * 0.20
            + liquidity_score * 0.35
        )

        if stability >= 0.75:
            status = "STABLE"
        elif stability >= 0.55:
            status = "WATCH"
        else:
            status = "AT_RISK"

        return ExecutiveFinancialReport(
            wage_to_revenue_ratio=wage_ratio,
            transfer_balance_ratio=transfer_ratio,
            liquidity_score=liquidity_score,
            stability_score=stability,
            status=status,
        )
