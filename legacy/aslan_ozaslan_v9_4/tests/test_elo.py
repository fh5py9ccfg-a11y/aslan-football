import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.ratings import EloRatingSystem

class EloTests(unittest.TestCase):
    def test_home_advantage_increases_expected_score(self):
        system = EloRatingSystem(home_advantage=80)
        home, away = system.expected_scores(1500, 1500)
        self.assertGreater(home, 0.5)
        self.assertLess(away, 0.5)

    def test_winner_gains_rating(self):
        system = EloRatingSystem(k_factor=20, home_advantage=0)
        result = system.update(1500, 1500, "HOME")
        self.assertGreater(result.home_after, 1500)
        self.assertLess(result.away_after, 1500)

if __name__ == "__main__":
    unittest.main()
