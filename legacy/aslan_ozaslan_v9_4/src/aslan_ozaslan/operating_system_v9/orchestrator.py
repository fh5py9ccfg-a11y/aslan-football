from __future__ import annotations
from collections import defaultdict

from .domain import OrchestratedDecision

class FootballDecisionOrchestrator:
    def __init__(
        self,
        *,
        expert_weights: dict[str, float] | None = None,
        minimum_consensus: float = 0.55,
        maximum_risk: float = 0.70,
    ):
        self.expert_weights = expert_weights or {}
        self.minimum_consensus = minimum_consensus
        self.maximum_risk = maximum_risk

    def combine(
        self,
        *,
        subject_id: str,
        decisions: tuple,
        safe_mode: bool = False,
    ) -> OrchestratedDecision:
        if not subject_id.strip():
            raise ValueError("subject_id boş olamaz")
        if not decisions:
            raise ValueError("En az bir uzman kararı gerekir")

        grouped = defaultdict(list)
        for decision in decisions:
            decision.validate()
            weight = self.expert_weights.get(decision.expert, 1.0)
            grouped[decision.recommendation].append((decision, weight))

        def score(item):
            recommendation, entries = item
            weighted = sum(
                decision.confidence * (1.0 - decision.risk) * weight
                for decision, weight in entries
            )
            return weighted, len(entries), recommendation

        final_recommendation, selected = max(
            grouped.items(),
            key=score,
        )

        selected_weight = sum(weight for _, weight in selected)
        confidence = (
            sum(decision.confidence * weight for decision, weight in selected)
            / selected_weight
        )
        risk = (
            sum(decision.risk * weight for decision, weight in selected)
            / selected_weight
        )

        total_weight = sum(
            weight
            for entries in grouped.values()
            for _, weight in entries
        )
        supporting_weight = sum(weight for _, weight in selected)
        consensus = supporting_weight / total_weight if total_weight else 0.0

        dissenting = tuple(sorted(
            decision.expert
            for recommendation, entries in grouped.items()
            if recommendation != final_recommendation
            for decision, _ in entries
        ))
        rationale = tuple(
            decision.rationale
            for decision, _ in selected
        )

        approved = (
            not safe_mode
            and consensus >= self.minimum_consensus
            and risk <= self.maximum_risk
        )

        return OrchestratedDecision(
            subject_id=subject_id,
            final_recommendation=final_recommendation,
            confidence=confidence,
            risk=risk,
            consensus_score=consensus,
            dissenting_experts=dissenting,
            rationale=rationale,
            approved=approved,
        )
