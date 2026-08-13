import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.audit import AuditRepository

class AuditRepositoryTests(unittest.TestCase):
    def test_append_and_list(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = AuditRepository(Path(directory) / "audit.db")
            repo.append(
                actor_id="admin-1",
                action="retry_dead_letter",
                resource_type="job",
                resource_id="job-1",
                payload={"reason":"manual"},
            )
            records = repo.list_recent()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].actor_id, "admin-1")

if __name__ == "__main__":
    unittest.main()
