from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LoanPlan:
    suitability_score: float
    recommendation: str
    target_level: str
    reasons: tuple[str, ...]

class LoanSuitabilityPlanner:
    def evaluate(
        self,
        *,
        age: int,
        current_level: float,
        first_team_readiness: float,
        minutes_share: float,
        growth_rate: float,
    ) -> LoanPlan:
        if not 14 <= age <= 23:
            raise ValueError("age geçersiz")
        for value in (
            current_level,
            first_team_readiness,
            minutes_share,
            growth_rate,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Kiralık plan girdileri geçersiz")

        need_for_minutes = 1.0 - minutes_share
        readiness_gap = max(0.0, 0.78 - first_team_readiness)
        suitability = min(
            need_for_minutes * 0.55
            + readiness_gap * 0.25
            + growth_rate * 0.20,
            1.0,
        )

        reasons = []
        if minutes_share < 0.35:
            reasons.append("competitive_minutes_needed")
        if first_team_readiness < 0.70:
            reasons.append("first_team_gap_exists")
        if growth_rate >= 0.08:
            reasons.append("development_momentum_should_continue")

        if suitability >= 0.68:
            recommendation = "LOAN"
        elif suitability >= 0.48:
            recommendation = "CONSIDER_LOAN"
        else:
            recommendation = "KEEP_IN_CLUB"

        if current_level >= 0.72:
            target_level = "TOP_DIVISION"
        elif current_level >= 0.58:
            target_level = "SECOND_TIER"
        else:
            target_level = "DEVELOPMENT_LEAGUE"

        return LoanPlan(
            suitability_score=suitability,
            recommendation=recommendation,
            target_level=target_level,
            reasons=tuple(reasons or ("current_pathway_is_sufficient",)),
        )
