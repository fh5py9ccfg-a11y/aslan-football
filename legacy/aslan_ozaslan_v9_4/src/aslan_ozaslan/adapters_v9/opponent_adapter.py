from __future__ import annotations

from .base import ExpertAdapter

class OpponentIntelligenceAdapter(ExpertAdapter):
    name = "opponent_intelligence"
    category = "MATCH_PREPARATION"

    def __init__(self, service):
        self.service = service

    def evaluate(self, context):
        context.validate()
        if context.decision_type != "MATCH_PLAN":
            return self._decision(
                recommendation="ABSTAIN",
                confidence=1.0,
                risk=0.0,
                rationale="Karar türü maç planı değil.",
            )

        report = self.service.prepare(
            opponent_dna=context.payload["opponent_dna"],
            matchups=context.payload["matchups"],
            attack_strength=context.payload["attack_strength"],
            defense_strength=context.payload["defense_strength"],
            iterations=context.payload.get("iterations", 2000),
            seed=context.payload.get("seed", 1),
        )

        critical_count = len(report.critical_matchups)
        weakness_values = (
            report.weakness_map.left_defense,
            report.weakness_map.right_defense,
            report.weakness_map.central_defense,
            report.weakness_map.transition_defense,
            report.weakness_map.set_piece_defense,
        )
        confidence = (
            max(weakness_values) * 0.60
            + min(critical_count / 4.0, 1.0) * 0.40
        ) * context.reliability_score
        risk = max(0.0, 1.0 - confidence) * 0.55

        return self._decision(
            recommendation=report.recommended_plan,
            confidence=confidence,
            risk=risk,
            rationale=report.briefing,
        )
