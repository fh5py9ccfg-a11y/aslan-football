import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.transfer_v8 import (
    TransferPlayerProfile,
    AgeCurveModel,
    InjuryRiskModel,
    TransferEconomicsModel,
    TransferIntelligenceService,
    PlayerVector,
    SimilarPlayerFinder,
)
from aslan_ozaslan.admin.transfer_intelligence_page import (
    render_transfer_intelligence_page,
)

class TransferIntelligenceTests(unittest.TestCase):
    def profile(self):
        return TransferPlayerProfile(
            player_id="p1",
            name="Oyuncu Bir",
            position="MF",
            age=24,
            current_value_score=8.2,
            form_trend=1.0,
            injury_days_last_365=18,
            minutes_last_365=2800,
            annual_salary=2_000_000,
            estimated_fee=12_000_000,
            contract_months_remaining=18,
            league_strength=0.78,
        )

    def test_age_curve_injury_and_economics(self):
        self.assertGreater(
            AgeCurveModel().score(age=24, position="MF"),
            0.8,
        )
        injury = InjuryRiskModel().evaluate(
            injury_days_last_365=18,
            minutes_last_365=2800,
        )
        self.assertEqual(injury.label, "LOW")

        economics = TransferEconomicsModel().evaluate(
            value_score=8.0,
            annual_salary=2_000_000,
            estimated_fee=12_000_000,
        )
        self.assertGreater(economics.score, 0)

    def test_assessment_and_page(self):
        profile = self.profile()
        assessment = TransferIntelligenceService().assess(profile)
        self.assertGreater(assessment.overall_score, 0.60)
        self.assertIn(
            assessment.recommendation,
            {"STRONG_BUY", "BUY_WITH_REVIEW", "WATCHLIST"},
        )

        page = render_transfer_intelligence_page(
            profile,
            assessment,
        )
        self.assertIn("Transfer Intelligence", page)
        self.assertIn("Maliyet verimi", page)
        self.assertIn("Öneri", page)

    def test_similar_player_finder(self):
        target = PlayerVector("p1", (0.8, 0.7, 0.6))
        candidates = [
            PlayerVector("p2", (0.79, 0.69, 0.61)),
            PlayerVector("p3", (0.20, 0.30, 0.40)),
        ]
        results = SimilarPlayerFinder().find(
            target,
            candidates,
            limit=2,
        )
        self.assertEqual(results[0].player_id, "p2")
        self.assertGreater(
            results[0].similarity,
            results[1].similarity,
        )

if __name__ == "__main__":
    unittest.main()
