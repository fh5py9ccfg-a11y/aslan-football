import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.explainability_v5 import (
    ExplanationFactor,
    ModelVote,
    ContributionNormalizer,
    EnsembleConsensusAnalyzer,
    ExplainablePredictionService,
)
from aslan_ozaslan.admin.explainability_page import render_explainability_page

class ExplainableAITests(unittest.TestCase):
    def factors(self):
        return [
            ExplanationFactor("Elo farkı",0.24,0.95,"strength"),
            ExplanationFactor("Form",0.17,0.90,"form"),
            ExplanationFactor("İç saha",0.09,1.00,"context"),
            ExplanationFactor("Kadro kalitesi",0.15,0.85,"squad"),
            ExplanationFactor("Chemistry",0.08,0.80,"squad"),
            ExplanationFactor("Taktik eşleşme",0.12,0.88,"tactics"),
            ExplanationFactor("Yorgunluk",-0.05,0.92,"fitness"),
            ExplanationFactor("Eksik oyuncular",-0.07,0.90,"availability"),
        ]

    def votes(self):
        return [
            ModelVote("elo",0.62,0.23,0.15),
            ModelVote("poisson",0.58,0.25,0.17),
            ModelVote("tactical",0.60,0.24,0.16),
        ]

    def test_contributions_are_normalized(self):
        factors = ContributionNormalizer().normalize(self.factors())
        self.assertAlmostEqual(
            sum(item.absolute_share for item in factors),
            1.0,
        )
        self.assertTrue(any(item.signed_share < 0 for item in factors))

    def test_consensus_is_high_for_close_models(self):
        report = EnsembleConsensusAnalyzer().analyze(self.votes())
        self.assertEqual(report.dominant_outcome, "HOME")
        self.assertEqual(report.confidence_label, "HIGH")

    def test_full_explainable_report_and_page(self):
        report = ExplainablePredictionService().build(
            outcome="HOME",
            probability=0.61,
            factors=self.factors(),
            model_votes=self.votes(),
            calibration_error=0.03,
            sample_adequacy=0.92,
            data_freshness=0.88,
            simulation_stability=0.90,
        )
        self.assertEqual(report.reliability.label, "HIGH")
        self.assertIn("ev sahibi galibiyeti", report.narrative)
        self.assertIn("Elo farkı", report.narrative)

        page = render_explainability_page(report)
        self.assertIn("Explainable Football AI", page)
        self.assertIn("Faktör katkıları", page)
        self.assertIn("Model fikir birliği", page)

if __name__ == "__main__":
    unittest.main()
