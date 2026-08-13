import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import (
    SecretRotationPolicy,
    SecretRotationPlanner,
    SecretRotationExecutor,
)

class FakeProvider:
    def __init__(self):
        self.calls = []
    def create_version(self, name):
        self.calls.append(("create", name))
        return "v2"
    def activate_version(self, name, version):
        self.calls.append(("activate", name, version))
    def retire_previous(self, name):
        self.calls.append(("retire", name))

class RotationExecutorTests(unittest.TestCase):
    def test_rotation_execution(self):
        now = datetime(2026, 7, 31, tzinfo=timezone.utc)
        decision = SecretRotationPlanner().plan(
            SecretRotationPolicy("session", 30, 24),
            last_rotated_at=now - timedelta(days=31),
            now=now,
        )
        provider = FakeProvider()
        result = SecretRotationExecutor(provider).execute(
            "SESSION_SECRET",
            decision,
            retire_previous=True,
        )
        self.assertTrue(result.activated)
        self.assertTrue(result.previous_retired)
        self.assertEqual(result.new_version, "v2")

if __name__ == "__main__":
    unittest.main()
