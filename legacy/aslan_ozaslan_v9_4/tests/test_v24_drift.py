import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.monitoring import DriftDetector

class DriftTests(unittest.TestCase):
    def test_drift_is_triggered(self):
        alert = DriftDetector(0.10).detect_accuracy_drift(0.64, 0.50)
        self.assertTrue(alert.triggered)

    def test_small_change_is_not_drift(self):
        alert = DriftDetector(0.10).detect_accuracy_drift(0.64, 0.59)
        self.assertFalse(alert.triggered)

if __name__ == "__main__":
    unittest.main()
