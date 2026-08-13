from __future__ import annotations

from .base import ExpertAdapter

class ScoutIntelligenceAdapter(ExpertAdapter):
    name = "scout_intelligence"
    category = "SCOUT"

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

        assessment = self.service.assess(
            candidate=context.payload["candidate"],
            player_dna=context.payload["player_dna"],
            desired_dna=context.payload["desired_dna"],
            consistency=context.payload["consistency"],
            minutes_share=context.payload["minutes_share"],
        )

        mapping = {
            "PRIORITY_TARGET": "SIGN",
            "SCOUT_DEEPLY": "SIGN_WITH_REVIEW",
            "MONITOR": "MONITOR",
            "REJECT": "REJECT",
        }
        recommendation = mapping[assessment.recommendation]
        confidence = (
            assessment.club_fit_score * 0.35
            + assessment.projected_level_24m * 0.30
            + assessment.league_translation_score * 0.20
            + assessment.hidden_gem_score * 0.15
        ) * context.reliability_score

        return self._decision(
            recommendation=recommendation,
            confidence=confidence,
            risk=assessment.risk_score,
            rationale=(
                f"Kulüp uyumu {assessment.club_fit_score:.3f}; "
                f"24 aylık seviye {assessment.projected_level_24m:.3f}; "
                f"risk {assessment.risk_score:.3f}."
            ),
        )
