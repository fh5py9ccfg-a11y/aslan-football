from __future__ import annotations
from statistics import mean

from .domain import ClubPlayerContract, TransferScenarioResult

class TransferScenarioSimulator:
    def simulate(
        self,
        *,
        current_players: list[ClubPlayerContract],
        outgoing_player_ids: tuple[str, ...] = (),
        incoming_players: tuple[ClubPlayerContract, ...] = (),
        transfer_income: float = 0.0,
        transfer_spend: float = 0.0,
    ) -> TransferScenarioResult:
        if min(transfer_income, transfer_spend) < 0:
            raise ValueError("Transfer değerleri negatif olamaz")
        if not current_players:
            raise ValueError("Kadro boş olamaz")

        for player in current_players:
            player.validate()
        for player in incoming_players:
            player.validate()

        outgoing = set(outgoing_player_ids)
        remaining = [
            player for player in current_players
            if player.player_id not in outgoing
        ]
        resulting = remaining + list(incoming_players)

        if not resulting:
            raise ValueError("Senaryo sonunda kadro boş kalamaz")

        salary_before = sum(
            player.annual_salary for player in current_players
        )
        salary_after = sum(
            player.annual_salary for player in resulting
        )
        value_before = sum(
            player.market_value for player in current_players
        )
        value_after = sum(
            player.market_value for player in resulting
        )
        quality_before = mean(
            player.quality_score for player in current_players
        )
        quality_after = mean(
            player.quality_score for player in resulting
        )

        budget_delta = (
            transfer_income
            - transfer_spend
            + salary_before
            - salary_after
        )

        return TransferScenarioResult(
            total_salary_before=salary_before,
            total_salary_after=salary_after,
            total_value_before=value_before,
            total_value_after=value_after,
            average_quality_before=quality_before,
            average_quality_after=quality_after,
            budget_delta=budget_delta,
        )
