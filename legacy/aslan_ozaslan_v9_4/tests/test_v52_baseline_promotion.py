import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.validation_v5 import (
    FootballBacktestReport,
    BaselineComparator,
    CalibrationReport,
    LeakageReport,
)
from aslan_ozaslan.football import (
    ModelPromotionPolicy,
    FootballModelPromotionGate,
)
from aslan_ozaslan.admin.promotion_page import render_promotion_page

class BaselinePromotionTests(unittest.TestCase):
    def test_candidate_can_be_promoted(self):
        candidate = FootballBacktestReport(1000,0.58,0.52,0.94)
        baseline = FootballBacktestReport(1000,0.54,0.60,1.02)
        comparison = BaselineComparator().compare(candidate, baseline)
        decision = FootballModelPromotionGate().evaluate(
            policy=ModelPromotionPolicy(
                minimum_brier_improvement=0.05,
                maximum_calibration_error=0.04,
                minimum_samples=500,
            ),
            comparison=comparison,
            calibration=CalibrationReport((),0.03),
            leakage=LeakageReport(True,()),
            samples=1000,
        )
        self.assertTrue(decision.allowed)
        self.assertIn("Onaylandı", render_promotion_page(decision))

    def test_leakage_blocks_promotion(self):
        candidate = FootballBacktestReport(1000,0.58,0.52,0.94)
        baseline = FootballBacktestReport(1000,0.54,0.60,1.02)
        comparison = BaselineComparator().compare(candidate, baseline)
        decision = FootballModelPromotionGate().evaluate(
            policy=ModelPromotionPolicy(0.05,0.04,500),
            comparison=comparison,
            calibration=CalibrationReport((),0.03),
            leakage=LeakageReport(False,("final_score",)),
            samples=1000,
        )
        self.assertFalse(decision.allowed)
        self.assertIn("data_leakage_detected", decision.blockers)

if __name__ == "__main__":
    unittest.main()
