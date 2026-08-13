import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    DeploymentPolicyContext,
    DeploymentPolicyBundle,
)

class PolicyEngineTests(unittest.TestCase):
    def test_production_policy_blocks_missing_controls(self):
        decision = DeploymentPolicyBundle().evaluate(
            DeploymentPolicyContext(
                production=True,
                replicas=1,
                image_reference="registry/app:3.7",
                tls_enabled=False,
                external_secrets_enabled=False,
                network_policy_enabled=False,
            )
        )
        self.assertFalse(decision.allowed)
        self.assertGreaterEqual(len(decision.blockers), 4)

    def test_valid_policy(self):
        decision = DeploymentPolicyBundle().evaluate(
            DeploymentPolicyContext(
                production=True,
                replicas=2,
                image_reference="registry/app:3.7@" + "sha256:" + "a"*64,
                tls_enabled=True,
                external_secrets_enabled=True,
                network_policy_enabled=True,
            )
        )
        self.assertTrue(decision.allowed)
        self.assertEqual(decision.warnings, ())

if __name__ == "__main__":
    unittest.main()
