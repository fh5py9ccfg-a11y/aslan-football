import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.league_config import LeagueParameters, LeagueParameterRegistry

class LeagueRegistryTests(unittest.TestCase):
    def test_returns_registered_parameters(self):
        registry = LeagueParameterRegistry()
        registry.register(LeagueParameters("tr-super-lig",1.35,1.10,20,6))
        self.assertEqual(registry.get("tr-super-lig").minimum_team_samples, 6)

    def test_inactive_league_is_blocked(self):
        registry = LeagueParameterRegistry()
        registry.register(LeagueParameters("inactive",1.2,1.05,18,6,False))
        with self.assertRaises(RuntimeError):
            registry.get("inactive")

if __name__ == "__main__":
    unittest.main()
