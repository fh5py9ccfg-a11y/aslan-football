import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.admin import AdminDashboard

class AdminDashboardTests(unittest.TestCase):
    def test_snapshot(self):
        snapshot = AdminDashboard().build(
            provider_status="healthy",
            champion_model="m2",
            pending_fixtures=12,
            unsettled_predictions=4,
            drift_alerts=1,
            release_ready=False,
        )
        self.assertEqual(snapshot.champion_model, "m2")
        self.assertFalse(snapshot.release_ready)

if __name__ == "__main__":
    unittest.main()
