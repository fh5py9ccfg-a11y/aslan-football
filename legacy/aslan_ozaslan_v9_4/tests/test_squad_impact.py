import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.squad import PlayerAvailability, SquadImpactCalculator

class SquadImpactTests(unittest.TestCase):
    def test_missing_key_player_reduces_attack(self):
        impact = SquadImpactCalculator().calculate([
            PlayerAvailability("p1", 0.9, 0.20, 0.02, "OUT"),
            PlayerAvailability("p2", 0.8, 0.05, 0.15, "AVAILABLE"),
        ])
        self.assertLess(impact.attack_multiplier, 1.0)
        self.assertEqual(impact.unavailable_count, 1)

    def test_unknown_status_adds_uncertainty(self):
        impact = SquadImpactCalculator().calculate([
            PlayerAvailability("p1", 1.0, 0.10, 0.10, "UNKNOWN"),
        ])
        self.assertGreater(impact.uncertainty_penalty, 0.0)

if __name__ == "__main__":
    unittest.main()
