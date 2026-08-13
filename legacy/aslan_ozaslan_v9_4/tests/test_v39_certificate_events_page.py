import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import CertificateEventRecorder
from aslan_ozaslan.admin import render_certificate_events_page

class CertificateEventsPageTests(unittest.TestCase):
    def test_page_renders_event(self):
        recorder = CertificateEventRecorder()
        event = recorder.record(
            "aslan-cert",
            "ISSUED",
            "certificate issued",
        )
        page = render_certificate_events_page([event])
        self.assertIn("Sertifika Olay Geçmişi", page)
        self.assertIn("ISSUED", page)

if __name__ == "__main__":
    unittest.main()
