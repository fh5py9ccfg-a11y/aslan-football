import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.identity import TeamIdentityRegistry

class TeamIdentityRegistryTests(unittest.TestCase):
    def test_register_and_resolve(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = TeamIdentityRegistry(Path(directory) / "identity.db")
            registry.register(
                provider="provider-a", external_team_id="44",
                canonical_team_id="team-001", display_name="Örnek Takım",
            )
            self.assertEqual(registry.resolve("provider-a", "44"), "team-001")

    def test_conflicting_mapping_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            registry = TeamIdentityRegistry(Path(directory) / "identity.db")
            registry.register(provider="p", external_team_id="1", canonical_team_id="a", display_name="A")
            with self.assertRaises(ValueError):
                registry.register(provider="p", external_team_id="1", canonical_team_id="b", display_name="B")

if __name__ == "__main__":
    unittest.main()
