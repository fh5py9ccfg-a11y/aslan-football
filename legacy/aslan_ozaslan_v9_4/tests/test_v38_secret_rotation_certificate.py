import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import SecretRotationPolicy, SecretRotationPlanner
from aslan_ozaslan.operations import CertificateStatus, CertificateExpiryMonitor

class RotationCertificateTests(unittest.TestCase):
    def test_secret_rotation_due(self):
        now = datetime(2026, 7, 31, tzinfo=timezone.utc)
        decision = SecretRotationPlanner().plan(
            SecretRotationPolicy("session", 30, 24),
            last_rotated_at=now - timedelta(days=31),
            now=now,
        )
        self.assertTrue(decision.due)

    def test_certificate_warning(self):
        now = datetime(2026, 7, 31, tzinfo=timezone.utc)
        alert = CertificateExpiryMonitor().evaluate(
            CertificateStatus(
                "aslan.example",
                now + timedelta(days=20),
            ),
            now=now,
        )
        self.assertTrue(alert.expiring)
        self.assertEqual(alert.severity, "WARNING")

if __name__ == "__main__":
    unittest.main()
