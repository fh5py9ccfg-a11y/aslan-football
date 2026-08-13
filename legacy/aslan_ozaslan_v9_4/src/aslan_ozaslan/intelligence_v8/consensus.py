from __future__ import annotations
from collections import defaultdict

from .domain import AgentOpinion, TacticalRecommendation

class MultiAgentTacticalConsensus:
    def combine(
        self,
        opinions: tuple[AgentOpinion, ...],
    ) -> TacticalRecommendation:
        if not opinions:
            raise ValueError("En az bir ajan görüşü gerekir")

        grouped = defaultdict(list)
        for opinion in opinions:
            if not 0 <= opinion.confidence <= 1:
                raise ValueError("confidence geçersiz")
            if not 0 <= opinion.risk <= 1:
                raise ValueError("risk geçersiz")
            grouped[opinion.recommendation].append(opinion)

        def score(item):
            action, action_opinions = item
            return (
                sum(op.confidence * (1.0 - op.risk) for op in action_opinions),
                len(action_opinions),
                action,
            )

        action, selected = max(grouped.items(), key=score)
        total_weight = sum(op.confidence for op in selected)
        confidence = (
            sum(op.confidence * (1.0 - op.risk) for op in selected)
            / total_weight
            if total_weight else 0.0
        )
        risk = sum(op.risk for op in selected) / len(selected)

        urgency = (
            "HIGH" if confidence >= 0.75 and risk >= 0.45
            else "MEDIUM" if confidence >= 0.60
            else "LOW"
        )

        return TacticalRecommendation(
            action=action,
            confidence=confidence,
            risk=risk,
            urgency=urgency,
            rationale=tuple(op.rationale for op in selected),
            approved=False,
        )
