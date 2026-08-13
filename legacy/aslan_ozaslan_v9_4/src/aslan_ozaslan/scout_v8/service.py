from __future__ import annotations

from .domain import ScoutCandidate, ScoutAssessment
from .development import PlayerDevelopmentProjector
from .league_translation import LeagueTranslationModel
from .hidden_gem import HiddenGemDetector
from .fit import ClubFitEvaluator

class ScoutIntelligenceService:
    def __init__(
        self,
        *,
        development=None,
        league_translation=None,
        hidden_gem=None,
        fit_evaluator=None,
    ):
        self.development = (
            development or PlayerDevelopmentProjector()
        )
        self.league_translation = (
            league_translation or LeagueTranslationModel()
        )
        self.hidden_gem = hidden_gem or HiddenGemDetector()
        self.fit_evaluator = fit_evaluator or ClubFitEvaluator()

    def assess(
        self,
        *,
        candidate: ScoutCandidate,
        player_dna,
        desired_dna,
        consistency: float,
        minutes_share: float,
    ) -> ScoutAssessment:
        candidate.validate()

        club_fit = self.fit_evaluator.evaluate(
            player=player_dna,
            desired=desired_dna,
        )
        development = self.development.project(
            age=candidate.age,
            current_level=candidate.current_level,
            potential_level=candidate.potential_level,
            consistency=consistency,
            minutes_share=minutes_share,
        )
        translation = self.league_translation.evaluate(
            player_level=development.level_12m,
            source_strength=candidate.source_league_strength,
            target_strength=candidate.target_league_strength,
            adaptation_risk=candidate.adaptation_risk,
        )

        risk = min(
            candidate.injury_risk * 0.40
            + candidate.adaptation_risk * 0.35
            + candidate.discipline_risk * 0.25,
            1.0,
        )

        hidden_gem = self.hidden_gem.score(
            current_level=candidate.current_level,
            potential_level=candidate.potential_level,
            market_value=candidate.market_value,
            annual_salary=candidate.annual_salary,
            age=candidate.age,
            risk_score=risk,
        )

        total = (
            club_fit * 0.30
            + development.level_24m * 0.22
            + translation.score * 0.18
            + hidden_gem * 0.18
            + (1.0 - risk) * 0.12
        )

        reasons = [
            f"club_fit={club_fit:.3f}",
            f"projected_24m={development.level_24m:.3f}",
            f"league_translation={translation.score:.3f}",
            f"hidden_gem={hidden_gem:.3f}",
            f"risk={risk:.3f}",
        ]

        if total >= 0.76 and risk <= 0.40:
            recommendation = "PRIORITY_TARGET"
        elif total >= 0.63:
            recommendation = "SCOUT_DEEPLY"
        elif total >= 0.50:
            recommendation = "MONITOR"
        else:
            recommendation = "REJECT"

        return ScoutAssessment(
            player_id=candidate.player_id,
            club_fit_score=club_fit,
            projected_level_12m=development.level_12m,
            projected_level_24m=development.level_24m,
            league_translation_score=translation.score,
            hidden_gem_score=hidden_gem,
            risk_score=risk,
            recommendation=recommendation,
            reasons=tuple(reasons),
        )
