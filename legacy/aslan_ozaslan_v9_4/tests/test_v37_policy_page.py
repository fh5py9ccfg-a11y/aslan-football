import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    DeploymentPolicyContext,
    DeploymentPolicyBundle,
)
from aslan_ozaslan.admin import render_policy_page

class PolicyPageTests(unittest.TestCase):
    def test_page_renders_blocker(self):
        decision = DeploymentPolicyBundle().evaluate(
            DeploymentPolicyContext(
                production=True,
                replicas=1,
                image_reference="registry/app:latest",
                tls_enabled=False,
                external_secrets_enabled=False,
                network_policy_enabled=False,
            )
        )
        page = render_policy_page(decision)
        self.assertIn("Deployment Policy Sonucu", page)
        self.assertIn("Engellendi", page)

if __name__ == "__main__":
    unittest.main()
