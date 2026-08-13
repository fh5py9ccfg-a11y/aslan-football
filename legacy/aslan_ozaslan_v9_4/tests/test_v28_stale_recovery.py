import sys, tempfile, unittest, sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.jobs import SQLiteJobQueue, StaleJobRecovery

class StaleRecoveryTests(unittest.TestCase):
    def test_stale_running_job_returns_to_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "jobs.db"
            queue = SQLiteJobQueue(db)
            job = queue.enqueue("sync", {})
            queue.claim_next("worker-1")
            old = (datetime.now(timezone.utc) - timedelta(hours=1)).isoformat()
            with sqlite3.connect(db) as connection:
                connection.execute(
                    "UPDATE background_jobs SET updated_at=? WHERE job_id=?",
                    (old, job.job_id),
                )
            recovered = StaleJobRecovery(str(db), 60).recover()
            self.assertEqual(recovered, 1)
            self.assertEqual(queue.get(job.job_id).status, "PENDING")

if __name__ == "__main__":
    unittest.main()
