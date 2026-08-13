import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.backtest import evaluate_probabilities, expanding_time_splits

class BacktestTests(unittest.TestCase):
    def test_metrics(self):
        m = evaluate_probabilities([(0.7,0.2,0.1),(0.2,0.3,0.5)],[0,2])
        self.assertEqual(m.accuracy, 1.0)
        self.assertLess(m.log_loss, 1.0)

    def test_time_order(self):
        start = datetime(2026,1,1,tzinfo=timezone.utc)
        ts = [start+timedelta(days=i) for i in range(10)]
        splits = expanding_time_splits(ts, minimum_train_size=4, test_size=2)
        self.assertEqual(splits[0].train_indices,(0,1,2,3))
        self.assertEqual(splits[0].test_indices,(4,5))

if __name__ == "__main__":
    unittest.main()
