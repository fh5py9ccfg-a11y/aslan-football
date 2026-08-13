from __future__ import annotations
from dataclasses import replace

class TacticalRecommendationSafetyGate:
    def __init__(
        self,
        *,
        minimum_confidence: float = 0.65,
        maximum_risk: float = 0.70,
    ):
        if not 0 <= minimum_confidence <= 1:
            raise ValueError("minimum_confidence geçersiz")
        if not 0 <= maximum_risk <= 1:
            raise ValueError("maximum_risk geçersiz")
        self.minimum_confidence = minimum_confidence
        self.maximum_risk = maximum_risk

    def evaluate(
        self,
        recommendation,
        *,
        reliability_score: float,
        safe_mode: bool,
    ):
        if not 0 <= reliability_score <= 1:
            raise ValueError("reliability_score geçersiz")

        approved = (
            not safe_mode
            and reliability_score >= 0.60
            and recommendation.confidence >= self.minimum_confidence
            and recommendation.risk <= self.maximum_risk
            and recommendation.action != "MANUAL_REVIEW"
        )

        return replace(recommendation, approved=approved)
