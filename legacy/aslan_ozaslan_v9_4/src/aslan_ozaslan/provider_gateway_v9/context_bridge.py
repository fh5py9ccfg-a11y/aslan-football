from __future__ import annotations

from aslan_ozaslan.adapters_v9 import FootballDecisionContext

class ProviderDecisionContextBridge:
    def transfer_context(
        self,
        *,
        subject_id: str,
        profile,
        candidate,
        player_dna,
        desired_dna,
        consistency: float,
        minutes_share: float,
        reliability_score: float,
    ) -> FootballDecisionContext:
        return FootballDecisionContext(
            subject_id=subject_id,
            decision_type="TRANSFER",
            payload={
                "profile": profile,
                "candidate": candidate,
                "player_dna": player_dna,
                "desired_dna": desired_dna,
                "consistency": consistency,
                "minutes_share": minutes_share,
            },
            reliability_score=reliability_score,
        )

    def match_plan_context(
        self,
        *,
        subject_id: str,
        opponent_dna,
        matchups,
        attack_strength: float,
        defense_strength: float,
        reliability_score: float,
        iterations: int = 2000,
        seed: int = 1,
    ) -> FootballDecisionContext:
        return FootballDecisionContext(
            subject_id=subject_id,
            decision_type="MATCH_PLAN",
            payload={
                "opponent_dna": opponent_dna,
                "matchups": matchups,
                "attack_strength": attack_strength,
                "defense_strength": defense_strength,
                "iterations": iterations,
                "seed": seed,
            },
            reliability_score=reliability_score,
        )
