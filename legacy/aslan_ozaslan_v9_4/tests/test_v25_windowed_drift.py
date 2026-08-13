import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.monitoring.windowed_drift import WindowedDriftDetector

class WindowedDriftTests(unittest.TestCase):
    def test_multiple_metrics_trigger(self):
        detector = WindowedDriftDetector(minimum_window_size=2)
        baseline = detector.metrics([
            ((0.8,0.1,0.1),0),
            ((0.1,0.8,0.1),1),
        ])
        recent = detector.metrics([
            ((0.34,0.33,0.33),2),
            ((0.34,0.33,0.33),2),
        ])
        report = detector.compare(baseline, recent)
        self.assertTrue(report.triggered)
        self.assertIn("log_loss_increase", report.reasons)

if __name__ == "__main__":
    unittest.main()
