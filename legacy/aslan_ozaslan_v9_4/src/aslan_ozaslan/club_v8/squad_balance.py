from __future__ import annotations
from collections import Counter
from statistics import mean

from .domain import ClubPlayerContract, SquadPlanningReport

class SquadBalanceAnalyzer:
    def analyze(
        self,
        players: list[ClubPlayerContract],
    ) -> SquadPlanningReport:
        if not players:
            raise ValueError("Kadro boş olamaz")
        for player in players:
            player.validate()

        positions = Counter(player.position for player in players)
        depth_components = []
        for count in positions.values():
            depth_components.append(min(count / 2.0, 1.0))
        depth_score = sum(depth_components) / len(depth_components)

        ages = [player.age for player in players]
        average_age = mean(ages)
        young = sum(1 for age in ages if age <= 22) / len(ages)
        prime = sum(1 for age in ages if 23 <= age <= 29) / len(ages)
        senior = sum(1 for age in ages if age >= 30) / len(ages)

        age_balance_score = max(
            0.0,
            min(
                1.0
                - abs(young - 0.25) * 0.8
                - abs(prime - 0.55) * 0.6
                - abs(senior - 0.20) * 0.8,
                1.0,
            ),
        )

        expiring = sum(
            1 for player in players
            if player.contract_months_remaining <= 12
        )
        contract_risk = expiring / len(players)

        recommendations = []
        for position, count in sorted(positions.items()):
            if count < 2:
                recommendations.append(
                    f"{position} pozisyonunda kadro derinliği yetersiz"
                )
        if average_age >= 29:
            recommendations.append("Kadro yaşı yüksek; gençleştirme gerekli")
        if contract_risk >= 0.25:
            recommendations.append(
                "Sözleşmesi yaklaşan oyuncular için uzatma veya satış planı gerekli"
            )
        if not recommendations:
            recommendations.append("Kadro dengesi kabul edilebilir")

        return SquadPlanningReport(
            squad_size=len(players),
            average_age=average_age,
            total_salary=sum(player.annual_salary for player in players),
            total_market_value=sum(player.market_value for player in players),
            depth_score=depth_score,
            age_balance_score=age_balance_score,
            contract_risk_score=contract_risk,
            recommendations=tuple(recommendations),
        )
