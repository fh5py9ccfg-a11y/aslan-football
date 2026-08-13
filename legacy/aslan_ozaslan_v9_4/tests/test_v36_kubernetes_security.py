import sys, unittest, json, base64
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    KubernetesSecret,
    KubernetesConfig,
    KubernetesSecurityRenderer,
)

class KubernetesSecurityTests(unittest.TestCase):
    def test_secret_is_base64_encoded(self):
        renderer = KubernetesSecurityRenderer()
        payload = json.loads(renderer.render_secret(
            KubernetesSecret(
                "app-secrets",
                "aslan-prod",
                {"SESSION_SECRET":"secret-value"},
            )
        ))
        self.assertEqual(
            base64.b64decode(payload["data"]["SESSION_SECRET"]).decode(),
            "secret-value",
        )

    def test_config_map(self):
        renderer = KubernetesSecurityRenderer()
        payload = json.loads(renderer.render_config(
            KubernetesConfig(
                "app-config",
                "aslan-prod",
                {"ENVIRONMENT":"production"},
            )
        ))
        self.assertEqual(payload["kind"], "ConfigMap")

if __name__ == "__main__":
    unittest.main()
