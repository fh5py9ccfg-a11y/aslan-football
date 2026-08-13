from __future__ import annotations

from .base import ExpertAdapter

class TransferIntelligenceAdapter(ExpertAdapter):
    name = "transfer_intelligence"
    category = "TRANSFER"

    def __init__(self, service):
        self.service = service

    def evaluate(self, context):
        context.validate()
        if context.decision_type != "TRANSFER":
            return self._decision(
                recommendation="ABSTAIN",
                confidence=1.0,
                risk=0.0,
                rationale="Karar türü transfer değil.",
            )

        profile = context.payload["profile"]
        assessment = self.service.assess(profile)

        mapping = {
            "STRONG_BUY": "SIGN",
            "BUY_WITH_REVIEW": "SIGN_WITH_REVIEW",
            "WATCHLIST": "MONITOR",
            "PASS": "REJECT",
        }
        recommendation = mapping[assessment.recommendation]
        confidence = assessment.overall_score * context.reliability_score
        risk = min(
            1.0,
            assessment.injury_risk_score * 0.55
            + (1.0 - assessment.cost_efficiency_score) * 0.45,
        )

        return self._decision(
            recommendation=recommendation,
            confidence=confidence,
            risk=risk,
            rationale=(
                f"Transfer skoru {assessment.overall_score:.3f}; "
                f"öneri {assessment.recommendation}."
            ),
        )
