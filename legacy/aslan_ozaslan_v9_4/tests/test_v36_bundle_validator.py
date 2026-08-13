import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import DeploymentBundleValidator

class BundleValidatorTests(unittest.TestCase):
    def test_missing_kinds_are_reported(self):
        report = DeploymentBundleValidator().validate([
            json.dumps({
                "kind":"Namespace",
                "metadata":{"name":"aslan"},
            }),
        ])
        self.assertFalse(report.valid)
        self.assertIn("missing_kind:Deployment", report.errors)

    def test_immutable_deployment(self):
        image = "registry/app:3.6@" + "sha256:" + "a"*64
        docs = [
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
        self.assertTrue(DeploymentBundleValidator().validate(docs).valid)

if __name__ == "__main__":
    unittest.main()
