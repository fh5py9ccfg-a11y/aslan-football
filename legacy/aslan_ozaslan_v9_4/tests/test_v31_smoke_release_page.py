import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import (
    SmokeTestRunner,
    ReadinessItem,
    ProductionReadinessEvaluator,
)
from aslan_ozaslan.admin import render_release_page

class SmokeReleasePageTests(unittest.TestCase):
    def test_release_page_ready(self):
        readiness = ProductionReadinessEvaluator().evaluate([
            ReadinessItem("tests", True, True, "ok"),
            ReadinessItem("database", True, True, "ok"),
        ])
        smoke = SmokeTestRunner().run({
            "health": lambda: True,
            "database": lambda: True,
        })
        page = render_release_page(
            readiness_report=readiness,
            smoke_report=smoke,
            artifact=None,
        )
        self.assertIn("Release durumu: Hazır", page)

    def test_failed_probe_blocks(self):
        smoke = SmokeTestRunner().run({
            "health": lambda: False,
        })
        self.assertFalse(smoke.passed)

if __name__ == "__main__":
    unittest.main()
