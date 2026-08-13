import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    ExternalSecretRef,
    ExternalSecretConfig,
    ExternalSecretRenderer,
    CertificateConfig,
    CertificateRenderer,
)

class ExternalSecretsCertTests(unittest.TestCase):
    def test_external_secret(self):
        payload = json.loads(ExternalSecretRenderer().render(
            ExternalSecretConfig(
                name="app-secrets",
                namespace="aslan-prod",
                secret_store_name="vault",
                target_secret_name="app-runtime",
                refresh_interval="1h",
                refs=(
                    ExternalSecretRef(
                        "SESSION_SECRET",
                        "aslan/production",
                        "session_secret",
                    ),
                ),
            )
        ))
        self.assertEqual(payload["kind"], "ExternalSecret")

    def test_certificate(self):
        payload = json.loads(CertificateRenderer().render(
            CertificateConfig(
                name="aslan-cert",
                namespace="aslan-prod",
                secret_name="aslan-tls",
                dns_names=("aslan.example",),
                issuer_name="letsencrypt",
            )
        ))
        self.assertEqual(payload["kind"], "Certificate")
        self.assertEqual(payload["spec"]["privateKey"]["rotationPolicy"], "Always")

if __name__ == "__main__":
    unittest.main()
