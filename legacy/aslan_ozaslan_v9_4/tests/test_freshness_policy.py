import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.services import FreshnessPolicy

class FreshnessPolicyTests(unittest.TestCase):
    def test_accepts_recent_data(self):
        now = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)
        result = FreshnessPolicy(180).evaluate(now - timedelta(minutes=30), now)
        self.assertTrue(result.accepted)

    def test_rejects_stale_data(self):
        now = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)
        result = FreshnessPolicy(180).evaluate(now - timedelta(hours=5), now)
        self.assertFalse(result.accepted)

if __name__ == "__main__":
    unittest.main()
