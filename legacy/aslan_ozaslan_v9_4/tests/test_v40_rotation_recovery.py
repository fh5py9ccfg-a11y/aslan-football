import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import SecretRotationRecovery

class FakeProvider:
    def __init__(self):
        self.calls = []
    def deactivate_version(self, name, version):
        self.calls.append(("deactivate", name, version))
    def reactivate_previous(self, name):
        self.calls.append(("reactivate", name))

class RotationRecoveryTests(unittest.TestCase):
    def test_recovery_reactivates_previous(self):
        provider = FakeProvider()
        result = SecretRotationRecovery(provider).recover(
            secret_name="SESSION_SECRET",
            failed_version="v2",
            previous_retired=True,
        )
        self.assertTrue(result.recovered)
        self.assertIn("previous-version-reactivated", result.steps)

if __name__ == "__main__":
    unittest.main()
