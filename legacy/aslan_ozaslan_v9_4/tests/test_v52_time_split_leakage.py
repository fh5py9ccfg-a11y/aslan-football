import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.validation_v5 import (
    TimedSample,
    ExpandingWindowSplitter,
    FeatureTimestamp,
    DataLeakageGuard,
)

class TimeSplitLeakageTests(unittest.TestCase):
    def test_expanding_window_split(self):
        start = datetime(2026,1,1,tzinfo=timezone.utc)
        samples = [
            TimedSample(str(index), start + timedelta(days=index))
            for index in range(10)
        ]
        splits = ExpandingWindowSplitter().split(
            samples,
            minimum_train_size=4,
            validation_size=2,
            step_size=2,
        )
        self.assertEqual(len(splits), 3)
        self.assertEqual(splits[0].train_ids, ("0","1","2","3"))
        self.assertEqual(splits[0].validation_ids, ("4","5"))

    def test_leakage_is_detected(self):
        prediction_time = datetime(2026,1,10,tzinfo=timezone.utc)
        report = DataLeakageGuard().evaluate(
            prediction_time=prediction_time,
            features=[
                FeatureTimestamp("form", prediction_time - timedelta(hours=2)),
                FeatureTimestamp("final_score", prediction_time + timedelta(hours=3)),
            ],
        )
        self.assertFalse(report.safe)
        self.assertEqual(report.leaked_features, ("final_score",))

if __name__ == "__main__":
    unittest.main()
