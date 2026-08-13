import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import ServiceLevelObjective, SLOEvaluator
from aslan_ozaslan.admin import render_slo_page

class SloPageTests(unittest.TestCase):
    def test_page_renders(self):
        evaluation = SLOEvaluator().evaluate(
            ServiceLevelObjective("availability", 0.999, 30),
            0.998,
        )
        page = render_slo_page([evaluation])
        self.assertIn("Servis Seviyesi Hedefleri", page)
        self.assertIn("FAIL", page)

if __name__ == "__main__":
    unittest.main()
