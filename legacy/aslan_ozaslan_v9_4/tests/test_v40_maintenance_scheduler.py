import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import MaintenanceTask, MaintenanceScheduler

class MaintenanceSchedulerTests(unittest.TestCase):
    def test_critical_failure_marks_unhealthy(self):
        report = MaintenanceScheduler().run([
            MaintenanceTask("audit", lambda: True, True),
            MaintenanceTask("certificate", lambda: False, True),
            MaintenanceTask("optional", lambda: False, False),
        ])
        self.assertFalse(report.healthy)
        self.assertEqual(len(report.results), 3)

if __name__ == "__main__":
    unittest.main()
