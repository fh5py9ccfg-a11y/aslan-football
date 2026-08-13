import sys, tempfile, sqlite3, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import CertificateEventRecorder, AuditVerificationJob
from aslan_ozaslan.audit import AppendOnlyAuditRepository

class CertificateAuditJobTests(unittest.TestCase):
    def test_certificate_events(self):
        recorder = CertificateEventRecorder()
        recorder.record("aslan-cert", "RENEWED", "renewal succeeded")
        self.assertEqual(recorder.recent()[0].event_type, "RENEWED")

    def test_audit_verification_job(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "audit.db"
            repo = AppendOnlyAuditRepository(db)
            repo.append(
                actor_id="admin",
                action="deploy",
                resource_type="release",
                resource_id="3.9",
                payload={},
            )
            result = AuditVerificationJob(repo).run()
            self.assertTrue(result.valid)

            with sqlite3.connect(db) as connection:
                connection.execute(
                    "UPDATE immutable_audit_records SET action='tampered' WHERE sequence_id=1"
                )
            result = AuditVerificationJob(repo).run()
            self.assertFalse(result.valid)

if __name__ == "__main__":
    unittest.main()
