import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import CanaryMetrics, CanaryEvaluator

class CanaryTests(unittest.TestCase):
    def test_good_canary_is_promoted(self):
        decision = CanaryEvaluator().evaluate(
            CanaryMetrics(200, 0.01, 500)
        )
        self.assertTrue(decision.promote)

    def test_bad_canary_is_rejected(self):
        decision = CanaryEvaluator().evaluate(
            CanaryMetrics(200, 0.05, 1500)
        )
        self.assertFalse(decision.promote)
        self.assertIn("error_rate_too_high", decision.reasons)
        self.assertIn("latency_too_high", decision.reasons)

if __name__ == "__main__":
    unittest.main()
