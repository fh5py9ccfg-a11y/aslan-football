import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.academy_v8 import (
    AcademyPlayer,
    YouthDevelopmentModel,
    FirstTeamReadinessEvaluator,
    LoanSuitabilityPlanner,
    AcademyIntelligenceService,
    AcademyNarrativeBuilder,
)
from aslan_ozaslan.admin.academy_intelligence_page import (
    render_academy_intelligence_page,
)

class AcademyIntelligenceTests(unittest.TestCase):
    def player(self):
        return AcademyPlayer(
            player_id="a1",
            name="Genç Oyuncu",
            position="MF",
            age=18,
            current_level=0.66,
            potential_level=0.88,
            training_attendance=0.94,
            match_minutes_share=0.42,
            physical_readiness=0.72,
            tactical_readiness=0.70,
            psychological_readiness=0.74,
            injury_risk=0.16,
            discipline_score=0.90,
        )

    def test_development_projection(self):
        projection = YouthDevelopmentModel().project(
            age=18,
            current_level=0.66,
            potential_level=0.88,
            attendance=0.94,
            minutes_share=0.42,
            discipline_score=0.90,
        )
        self.assertGreater(projection.level_12m, 0.66)
        self.assertGreater(projection.level_24m, projection.level_12m)

    def test_readiness_and_loan(self):
        readiness = FirstTeamReadinessEvaluator().evaluate(
            current_level=0.66,
            physical_readiness=0.72,
            tactical_readiness=0.70,
            psychological_readiness=0.74,
            injury_risk=0.16,
        )
        self.assertIn(readiness.label, {"NEAR_READY", "READY"})

        loan = LoanSuitabilityPlanner().evaluate(
            age=18,
            current_level=0.66,
            first_team_readiness=readiness.score,
            minutes_share=0.20,
            growth_rate=0.12,
        )
        self.assertIn(
            loan.recommendation,
            {"LOAN", "CONSIDER_LOAN"},
        )

    def test_full_assessment_narrative_and_page(self):
        player = self.player()
        assessment = AcademyIntelligenceService().assess(
            player,
            current_market_value=1_200_000,
        )
        self.assertGreater(
            assessment.projected_market_value_24m,
            1_200_000,
        )
        self.assertIn(
            assessment.pathway,
            {
                "PROMOTE_TO_FIRST_TEAM",
                "TRAIN_WITH_FIRST_TEAM",
                "LOAN_FOR_DEVELOPMENT",
                "HYBRID_DEVELOPMENT_PLAN",
                "CONTINUE_ACADEMY",
            },
        )

        narrative = AcademyNarrativeBuilder().build(
            player,
            assessment,
        )
        self.assertIn("A takım hazırlık skoru", narrative)

        page = render_academy_intelligence_page(
            player,
            assessment,
            narrative,
        )
        self.assertIn("Academy Intelligence", page)
        self.assertIn("Gelişim yolu", page)
        self.assertIn("Kiralık uygunluğu", page)

if __name__ == "__main__":
    unittest.main()
