from __future__ import annotations

from .base import ExpertAdapter

class ClubIntelligenceAdapter(ExpertAdapter):
    name = "club_intelligence"
    category = "SQUAD"

    def __init__(
        self,
        *,
        squad_analyzer,
        budget_analyzer,
        contract_analyzer,
        advisor,
    ):
        self.squad_analyzer = squad_analyzer
        self.budget_analyzer = budget_analyzer
        self.contract_analyzer = contract_analyzer
        self.advisor = advisor

    def evaluate(self, context):
        context.validate()
        if context.decision_type != "SQUAD_PLAN":
            return self._decision(
                recommendation="ABSTAIN",
                confidence=1.0,
                risk=0.0,
                rationale="Karar türü kadro planı değil.",
            )

        players = context.payload["players"]
        squad_report = self.squad_analyzer.analyze(players)
        budget_report = self.budget_analyzer.evaluate(
            context.payload["budget"]
        )
        contract_risks = tuple(
            self.contract_analyzer.evaluate(player)
            for player in players
        )
        advice = self.advisor.advise(
            squad_report=squad_report,
            budget_assessment=budget_report,
            contract_risks=contract_risks,
        )

        risk = min(
            1.0,
            squad_report.contract_risk_score * 0.40
            + (1.0 - squad_report.depth_score) * 0.25
            + (1.0 - squad_report.age_balance_score) * 0.20
            + min(budget_report.salary_utilization, 1.0) * 0.15,
        )
        confidence = (
            squad_report.depth_score * 0.35
            + squad_report.age_balance_score * 0.25
            + (1.0 - squad_report.contract_risk_score) * 0.20
            + (1.0 - min(budget_report.salary_utilization, 1.0)) * 0.20
        ) * context.reliability_score

        recommendation = (
            "REBUILD_SQUAD"
            if risk >= 0.65
            else "TARGETED_CHANGES"
            if risk >= 0.40
            else "MAINTAIN_CORE"
        )

        return self._decision(
            recommendation=recommendation,
            confidence=confidence,
            risk=risk,
            rationale=" | ".join(advice),
        )
