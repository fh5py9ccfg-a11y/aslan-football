import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import ControlCenterBuilder
from aslan_ozaslan.admin import render_control_center_page

class ControlCenterTests(unittest.TestCase):
    def test_ready_snapshot(self):
        snapshot = ControlCenterBuilder().build(
            health_ok=True,
            audit_chain_ok=True,
            certificate_alerts=0,
            dead_letter_jobs=0,
            drift_alerts=1,
            release_approved=True,
            policy_allowed=True,
            signed_bundle_valid=True,
        )
        self.assertTrue(snapshot.release_ready)
        page = render_control_center_page(snapshot)
        self.assertIn("Production Operasyon Kontrol Merkezi", page)
        self.assertIn("Genel release durumu: Hazır", page)

    def test_dead_letter_blocks_release(self):
        snapshot = ControlCenterBuilder().build(
            health_ok=True,
            audit_chain_ok=True,
            certificate_alerts=0,
            dead_letter_jobs=2,
            drift_alerts=0,
            release_approved=True,
            policy_allowed=True,
            signed_bundle_valid=True,
        )
        self.assertFalse(snapshot.release_ready)

if __name__ == "__main__":
    unittest.main()
