import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    NetworkRule,
    NetworkPolicyRenderer,
    IngressConfig,
    IngressRenderer,
)

class NetworkIngressTests(unittest.TestCase):
    def test_default_deny_and_allow(self):
        renderer = NetworkPolicyRenderer()
        deny = json.loads(renderer.render_default_deny("aslan-prod"))
        allow = json.loads(renderer.render_allow(
            "aslan-prod",
            NetworkRule("web", "api", 8000),
        ))
        self.assertEqual(deny["metadata"]["name"], "default-deny")
        self.assertEqual(allow["kind"], "NetworkPolicy")

    def test_ingress_requires_tls(self):
        payload = json.loads(IngressRenderer().render(
            IngressConfig(
                namespace="aslan-prod",
                host="aslan.example",
                service_name="web",
                service_port=8000,
                tls_secret_name="aslan-tls",
            )
        ))
        self.assertEqual(payload["spec"]["tls"][0]["secretName"], "aslan-tls")

if __name__ == "__main__":
    unittest.main()
