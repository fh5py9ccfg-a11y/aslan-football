import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.jobs import SQLiteJobQueue, JobWorker
from aslan_ozaslan.admin import DeadLetterRetryService

class DeadLetterRetryTests(unittest.TestCase):
    def test_dead_job_can_be_requeued(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "jobs.db"
            queue = SQLiteJobQueue(db)
            job = queue.enqueue("fail", {}, max_attempts=1)
            JobWorker(
                queue,
                {"fail": lambda payload: (_ for _ in ()).throw(RuntimeError("boom"))},
                "worker-1",
            ).run_once()
            self.assertEqual(queue.get(job.job_id).status, "DEAD")
            self.assertTrue(DeadLetterRetryService(str(db)).retry(job.job_id))
            self.assertEqual(queue.get(job.job_id).status, "PENDING")

if __name__ == "__main__":
    unittest.main()
