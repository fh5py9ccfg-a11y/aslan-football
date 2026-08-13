import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.deployment import ReleaseManager, RollbackPlanner

class ReleaseArtifactTests(unittest.TestCase):
    def test_manifest_and_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            artifact_path = Path(directory) / "release.zip"
            artifact_path.write_bytes(b"release-content")
            manager = ReleaseManager()
            artifact = manager.build_manifest("3.1", artifact_path)
            self.assertTrue(manager.verify(artifact))

    def test_rollback_plan(self):
        plan = RollbackPlanner().build("3.1", "3.0")
        self.assertIn("run-smoke-tests", plan.steps)

if __name__ == "__main__":
    unittest.main()
