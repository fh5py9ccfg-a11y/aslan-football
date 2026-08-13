import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import CertificateStatus, CertificateExpiryMonitor
from aslan_ozaslan.admin import render_certificate_page

class CertificatePageTests(unittest.TestCase):
    def test_page_renders_alert(self):
        now = datetime(2026, 7, 31, tzinfo=timezone.utc)
        alert = CertificateExpiryMonitor().evaluate(
            CertificateStatus("aslan.example", now + timedelta(days=5)),
            now=now,
        )
        page = render_certificate_page([alert])
        self.assertIn("Sertifika İzleme", page)
        self.assertIn("CRITICAL", page)

if __name__ == "__main__":
    unittest.main()
