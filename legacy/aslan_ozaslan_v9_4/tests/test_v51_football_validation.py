import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.validation_v5 import (
    MatchPredictionSample,
    FootballBacktester,
    ProbabilityCalibrationAnalyzer,
)
from aslan_ozaslan.ratings_v5 import (
    LeagueStrengthProfile,
    LeagueStrengthNormalizer,
)
from aslan_ozaslan.football import FootballModelRegistry
from aslan_ozaslan.admin.model_validation_page import render_model_validation_page

class FootballValidationTests(unittest.TestCase):
    def test_backtest_metrics(self):
        report = FootballBacktester().evaluate([
            MatchPredictionSample(0.70,0.20,0.10,"HOME"),
            MatchPredictionSample(0.20,0.30,0.50,"AWAY"),
            MatchPredictionSample(0.20,0.60,0.20,"DRAW"),
        ])
        self.assertEqual(report.accuracy, 1.0)
        self.assertGreater(report.brier_score, 0)
        self.assertGreater(report.log_loss, 0)

    def test_calibration_report(self):
        report = ProbabilityCalibrationAnalyzer().analyze(
            [0.1,0.2,0.8,0.9],
            [0,0,1,1],
            bins=2,
        )
        self.assertLess(report.expected_calibration_error, 0.2)

    def test_league_normalization(self):
        normalizer = LeagueStrengthNormalizer()
        tr = LeagueStrengthProfile("tr1",1500,100)
        eng = LeagueStrengthProfile("eng1",1600,80)
        self.assertAlmostEqual(normalizer.normalize(1600,tr),1.0)
        self.assertAlmostEqual(normalizer.compare(1600,tr,1600,eng),1.0)

    def test_model_registry_and_page(self):
        registry = FootballModelRegistry()
        v1 = registry.register(
            model_name="elo-matchup",
            version="5.1.0",
            league_id="tr1",
            brier_score=0.42,
            log_loss=0.91,
        )
        active = registry.activate("elo-matchup","5.1.0","tr1")
        self.assertTrue(active.active)

        backtest = FootballBacktester().evaluate([
            MatchPredictionSample(0.7,0.2,0.1,"HOME")
        ])
        calibration = ProbabilityCalibrationAnalyzer().analyze([0.7],[1],bins=2)
        page = render_model_validation_page(backtest, calibration)
        self.assertIn("Futbol Model Doğrulama", page)
        self.assertIn("Brier skoru", page)

if __name__ == "__main__":
    unittest.main()
