import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import (
    DeploymentBundleValidator,
    DeploymentBundleSigner,
    SignedDeploymentPipelineGate,
)

class SignedPipelineTests(unittest.TestCase):
    def documents(self):
        image = "registry/app:3.9@" + "sha256:" + "a"*64
        return [
            json.dumps({"kind":"Namespace","metadata":{"name":"aslan"}}),
            json.dumps({
                "kind":"Deployment",
                "metadata":{"name":"web"},
                "spec":{"template":{"spec":{"containers":[{"image":image}]}}},
            }),
            json.dumps({"kind":"Service","metadata":{"name":"web"}}),
            json.dumps({"kind":"Ingress","metadata":{"name":"web"}}),
            json.dumps({"kind":"NetworkPolicy","metadata":{"name":"deny"}}),
        ]

    def test_signed_valid_bundle_is_allowed(self):
        documents = self.documents()
        signer = DeploymentBundleSigner(b"k"*32, "ci")
        signed = signer.sign(documents)
        report = SignedDeploymentPipelineGate(
            DeploymentBundleValidator(),
            signer,
        ).evaluate(documents, signed)
        self.assertTrue(report.allowed)

    def test_tampered_bundle_is_blocked(self):
        documents = self.documents()
        signer = DeploymentBundleSigner(b"k"*32, "ci")
        signed = signer.sign(documents)
        documents.append(json.dumps({"kind":"ConfigMap","metadata":{"name":"x"}}))
        report = SignedDeploymentPipelineGate(
            DeploymentBundleValidator(),
            signer,
        ).evaluate(documents, signed)
        self.assertFalse(report.allowed)
        self.assertFalse(report.signature_valid)

if __name__ == "__main__":
    unittest.main()
