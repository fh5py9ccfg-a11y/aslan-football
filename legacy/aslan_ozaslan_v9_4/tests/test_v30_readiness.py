import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import ReadinessItem, ProductionReadinessEvaluator

class ReadinessTests(unittest.TestCase):
    def test_critical_failure_blocks(self):
        report = ProductionReadinessEvaluator().evaluate([
            ReadinessItem("tests", True, True, "ok"),
            ReadinessItem("database", False, True, "missing"),
            ReadinessItem("banner", False, False, "optional"),
        ])
        self.assertFalse(report.ready)
        self.assertIn("database", report.blockers)
        self.assertIn("banner", report.warnings)

if __name__ == "__main__":
    unittest.main()
