from __future__ import annotations

from .base import ExpertAdapter

class ExecutiveIntelligenceAdapter(ExpertAdapter):
    name = "executive_intelligence"
    category = "EXECUTIVE"

    def __init__(self, service):
        self.service = service

    def evaluate(self, context):
        context.validate()
        if context.decision_type != "EXECUTIVE":
            return self._decision(
                recommendation="ABSTAIN",
                confidence=1.0,
                risk=0.0,
                rationale="Karar türü yönetim değil.",
            )

        report = self.service.evaluate(
            snapshot=context.payload["snapshot"],
            objectives=context.payload["objectives"],
            cash_reserve=context.payload["cash_reserve"],
            annual_commitments=context.payload["annual_commitments"],
            contract_risk=context.payload["contract_risk"],
            sporting_volatility=context.payload["sporting_volatility"],
        )

        mapping = {
            "HEALTHY": "CONTINUE_STRATEGY",
            "WATCH": "CORRECTIVE_ACTION",
            "INTERVENTION_REQUIRED": "EXECUTIVE_INTERVENTION",
        }

        return self._decision(
            recommendation=mapping[report.status],
            confidence=report.health_score * context.reliability_score,
            risk=report.strategic_risk,
            rationale=" | ".join(report.priority_actions),
        )
