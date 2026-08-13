import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import HealthMonitor
from aslan_ozaslan.admin import render_operations_page

class OperationsPageTests(unittest.TestCase):
    def test_page_renders_status(self):
        report = HealthMonitor().run({
            "database": (lambda: True, True),
        })
        page = render_operations_page(
            metrics={"queue_depth": 1},
            dead_letters=[],
            health_report=report,
        )
        self.assertIn("Operasyon Paneli", page)
        self.assertIn("Sağlıklı", page)

if __name__ == "__main__":
    unittest.main()
