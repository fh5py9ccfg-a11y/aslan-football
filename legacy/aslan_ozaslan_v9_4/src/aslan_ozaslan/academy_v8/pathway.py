from __future__ import annotations

class AcademyPathwayPlanner:
    def decide(
        self,
        *,
        readiness_label: str,
        loan_recommendation: str,
        projected_level_12m: float,
    ) -> str:
        if readiness_label == "READY":
            return "PROMOTE_TO_FIRST_TEAM"
        if (
            readiness_label == "NEAR_READY"
            and projected_level_12m >= 0.72
        ):
            return "TRAIN_WITH_FIRST_TEAM"
        if loan_recommendation == "LOAN":
            return "LOAN_FOR_DEVELOPMENT"
        if loan_recommendation == "CONSIDER_LOAN":
            return "HYBRID_DEVELOPMENT_PLAN"
        return "CONTINUE_ACADEMY"
