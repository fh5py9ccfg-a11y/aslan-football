import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import DeploymentEnvironment, EnvironmentRegistry

class EnvironmentTests(unittest.TestCase):
    def test_production_requires_two_replicas(self):
        registry = EnvironmentRegistry()
        with self.assertRaises(ValueError):
            registry.register(DeploymentEnvironment(
                "production", 1, "primary", "prod", True
            ))

    def test_registry(self):
        registry = EnvironmentRegistry()
        registry.register(DeploymentEnvironment(
            "staging", 1, "staging", "stage", False
        ))
        self.assertEqual(registry.get("staging").redis_namespace, "stage")

if __name__ == "__main__":
    unittest.main()
