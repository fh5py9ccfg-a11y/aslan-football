from __future__ import annotations

class ClubAIAdvisor:
    def advise(
        self,
        *,
        squad_report,
        budget_assessment,
        contract_risks,
    ) -> tuple[str, ...]:
        recommendations = list(squad_report.recommendations)

        if budget_assessment.status == "CRITICAL":
            recommendations.append(
                "Maaş bütçesi kritik seviyede; yeni yüksek maaşlı transfer durdurulmalı"
            )
        elif budget_assessment.status == "TIGHT":
            recommendations.append(
                "Yeni transfer öncesinde maaş çıkışı planlanmalı"
            )

        critical_contracts = [
            risk.player_id
            for risk in contract_risks
            if risk.risk_level == "CRITICAL"
        ]
        if critical_contracts:
            recommendations.append(
                "Kritik sözleşmeler: " + ", ".join(critical_contracts)
            )

        return tuple(dict.fromkeys(recommendations))
