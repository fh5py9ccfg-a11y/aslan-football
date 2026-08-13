from __future__ import annotations
from dataclasses import dataclass

from .domain import ClubPlayerContract

@dataclass(frozen=True)
class ContractRisk:
    player_id: str
    risk_level: str
    recommended_action: str
    urgency_score: float

class ContractRiskAnalyzer:
    def evaluate(
        self,
        player: ClubPlayerContract,
    ) -> ContractRisk:
        player.validate()
        months = player.contract_months_remaining

        if months <= 6:
            return ContractRisk(
                player.player_id,
                "CRITICAL",
                "RENEW_OR_SELL_NOW",
                1.0,
            )
        if months <= 12:
            return ContractRisk(
                player.player_id,
                "HIGH",
                "START_RENEWAL_OR_SALE",
                0.82,
            )
        if months <= 24:
            return ContractRisk(
                player.player_id,
                "MEDIUM",
                "MONITOR_AND_PLAN",
                0.55,
            )
        return ContractRisk(
            player.player_id,
            "LOW",
            "NO_IMMEDIATE_ACTION",
            0.20,
        )
