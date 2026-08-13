import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import PipelineStage, DeploymentPipeline

class PipelineTests(unittest.TestCase):
    def test_critical_failure_stops_pipeline(self):
        called = []
        report = DeploymentPipeline().run([
            PipelineStage("tests", True, lambda: False),
            PipelineStage("deploy", True, lambda: called.append("deploy") or True),
        ])
        self.assertFalse(report.passed)
        self.assertEqual(called, [])
        self.assertEqual(len(report.results), 1)

    def test_noncritical_failure_does_not_block(self):
        report = DeploymentPipeline().run([
            PipelineStage("lint", False, lambda: False),
            PipelineStage("tests", True, lambda: True),
        ])
        self.assertTrue(report.passed)

if __name__ == "__main__":
    unittest.main()
