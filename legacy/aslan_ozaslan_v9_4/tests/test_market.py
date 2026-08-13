import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.market import OddsSnapshot, MarketAnalyzer

class MarketTests(unittest.TestCase):
    def test_implied_probabilities_sum_to_one(self):
        snapshot = OddsSnapshot(
            datetime.now(timezone.utc), 2.0, 3.4, 3.8, "bookmaker-a"
        )
        result = MarketAnalyzer().implied_probabilities(snapshot)
        self.assertAlmostEqual(result.home + result.draw + result.away, 1.0, places=5)
        self.assertGreater(result.overround, 0.0)

    def test_movement_requires_time_order(self):
        now = datetime.now(timezone.utc)
        first = OddsSnapshot(now, 2.0, 3.4, 3.8, "a")
        latest = OddsSnapshot(now + timedelta(hours=1), 1.9, 3.5, 4.0, "a")
        movement = MarketAnalyzer().movement(first, latest)
        self.assertLess(movement["home_change"], 0)

if __name__ == "__main__":
    unittest.main()
