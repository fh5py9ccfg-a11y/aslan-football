import sys, tempfile, sqlite3, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.audit import AppendOnlyAuditRepository

class AppendOnlyAuditTests(unittest.TestCase):
    def test_chain_verification(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "audit.db"
            repo = AppendOnlyAuditRepository(db)
            repo.append(
                actor_id="admin",
                action="deploy",
                resource_type="release",
                resource_id="3.7",
                payload={"ok":True},
            )
            repo.append(
                actor_id="admin",
                action="rollback",
                resource_type="release",
                resource_id="3.6",
                payload={"reason":"test"},
            )
            self.assertTrue(repo.verify_chain())

            with sqlite3.connect(db) as connection:
                connection.execute(
                    "UPDATE immutable_audit_records SET action='tampered' WHERE sequence_id=1"
                )
            self.assertFalse(repo.verify_chain())

if __name__ == "__main__":
    unittest.main()
