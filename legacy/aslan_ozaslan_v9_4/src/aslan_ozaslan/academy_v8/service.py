from __future__ import annotations

from .domain import AcademyPlayer, AcademyAssessment
from .development import YouthDevelopmentModel
from .readiness import FirstTeamReadinessEvaluator
from .loan import LoanSuitabilityPlanner
from .valuation import AcademyValuationModel
from .pathway import AcademyPathwayPlanner

class AcademyIntelligenceService:
    def __init__(
        self,
        *,
        development=None,
        readiness=None,
        loan_planner=None,
        valuation=None,
        pathway=None,
    ):
        self.development = development or YouthDevelopmentModel()
        self.readiness = readiness or FirstTeamReadinessEvaluator()
        self.loan_planner = loan_planner or LoanSuitabilityPlanner()
        self.valuation = valuation or AcademyValuationModel()
        self.pathway = pathway or AcademyPathwayPlanner()

    def assess(
        self,
        player: AcademyPlayer,
        *,
        current_market_value: float,
    ) -> AcademyAssessment:
        player.validate()

        development = self.development.project(
            age=player.age,
            current_level=player.current_level,
            potential_level=player.potential_level,
            attendance=player.training_attendance,
            minutes_share=player.match_minutes_share,
            discipline_score=player.discipline_score,
        )
        readiness = self.readiness.evaluate(
            current_level=player.current_level,
            physical_readiness=player.physical_readiness,
            tactical_readiness=player.tactical_readiness,
            psychological_readiness=player.psychological_readiness,
            injury_risk=player.injury_risk,
        )
        loan = self.loan_planner.evaluate(
            age=player.age,
            current_level=player.current_level,
            first_team_readiness=readiness.score,
            minutes_share=player.match_minutes_share,
            growth_rate=development.growth_rate,
        )
        projected_value = self.valuation.project_24m(
            current_market_value=current_market_value,
            projected_level_24m=development.level_24m,
            age=player.age,
            first_team_readiness=readiness.score,
            injury_risk=player.injury_risk,
        )
        pathway = self.pathway.decide(
            readiness_label=readiness.label,
            loan_recommendation=loan.recommendation,
            projected_level_12m=development.level_12m,
        )

        development_score = (
            development.level_24m * 0.45
            + development.growth_rate * 0.30
            + player.discipline_score * 0.15
            + player.training_attendance * 0.10
        )

        risks = list(readiness.blockers)
        if player.injury_risk >= 0.45:
            risks.append("injury_monitoring_required")
        if player.match_minutes_share < 0.25:
            risks.append("competitive_minutes_low")

        return AcademyAssessment(
            player_id=player.player_id,
            development_score=max(0.0, min(development_score, 1.0)),
            first_team_readiness=readiness.score,
            loan_suitability=loan.suitability_score,
            projected_level_12m=development.level_12m,
            projected_market_value_24m=projected_value,
            pathway=pathway,
            risks=tuple(dict.fromkeys(risks)),
        )
