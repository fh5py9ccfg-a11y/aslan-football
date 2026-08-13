from __future__ import annotations

from .base import ExpertAdapter

class AcademyIntelligenceAdapter(ExpertAdapter):
    name = "academy_intelligence"
    category = "ACADEMY"

    def __init__(self, service):
        self.service = service

    def evaluate(self, context):
        context.validate()
        if context.decision_type != "ACADEMY":
            return self._decision(
                recommendation="ABSTAIN",
                confidence=1.0,
                risk=0.0,
                rationale="Karar türü akademi değil.",
            )

        player = context.payload["player"]
        assessment = self.service.assess(
            player,
            current_market_value=context.payload["current_market_value"],
        )

        mapping = {
            "PROMOTE_TO_FIRST_TEAM": "PROMOTE",
            "TRAIN_WITH_FIRST_TEAM": "INTEGRATE",
            "LOAN_FOR_DEVELOPMENT": "LOAN",
            "HYBRID_DEVELOPMENT_PLAN": "HYBRID_PLAN",
            "CONTINUE_ACADEMY": "CONTINUE_DEVELOPMENT",
        }
        recommendation = mapping[assessment.pathway]
        confidence = (
            assessment.development_score * 0.40
            + assessment.first_team_readiness * 0.40
            + (1.0 - min(assessment.loan_suitability, 1.0)) * 0.20
        ) * context.reliability_score
        risk = min(
            1.0,
            len(assessment.risks) * 0.18
            + max(0.0, 0.65 - assessment.first_team_readiness),
        )

        return self._decision(
            recommendation=recommendation,
            confidence=confidence,
            risk=risk,
            rationale=(
                f"Gelişim yolu {assessment.pathway}; "
                f"A takım hazırlığı {assessment.first_team_readiness:.3f}."
            ),
        )
