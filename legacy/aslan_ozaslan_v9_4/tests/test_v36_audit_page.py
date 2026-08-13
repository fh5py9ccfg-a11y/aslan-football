import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.audit import AuditRecord
from aslan_ozaslan.admin import render_audit_page

class AuditPageTests(unittest.TestCase):
    def test_page_renders_record(self):
        page = render_audit_page([
            AuditRecord(
                "a1",
                "admin",
                "deploy",
                "release",
                "3.6",
                {},
                "2026-07-31T09:00:00+00:00",
            )
        ])
        self.assertIn("Denetim Kayıtları", page)
        self.assertIn("deploy", page)

if __name__ == "__main__":
    unittest.main()
