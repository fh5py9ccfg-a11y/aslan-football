import sys, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.audit import build_postgres_audit_contract
from aslan_ozaslan.deployment import DeploymentBundleSigner

class AuditSigningTests(unittest.TestCase):
    def test_postgres_contract(self):
        contract = build_postgres_audit_contract()
        self.assertIn("append-only-role", contract.protections)
        self.assertIn("INSERT INTO immutable_audit_records", contract.insert_sql)

    def test_bundle_sign_and_verify(self):
        documents = [
            json.dumps({"kind":"Namespace","metadata":{"name":"aslan"}}),
            json.dumps({"kind":"Service","metadata":{"name":"web"}}),
        ]
        signer = DeploymentBundleSigner(b"k"*32, "ci")
        signed = signer.sign(documents)
        self.assertTrue(signer.verify(documents, signed))
        tampered = documents + [json.dumps({"kind":"ConfigMap","metadata":{"name":"x"}})]
        self.assertFalse(signer.verify(tampered, signed))

if __name__ == "__main__":
    unittest.main()
