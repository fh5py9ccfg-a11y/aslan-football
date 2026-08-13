import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.jobs import SQLiteJobQueue, JobWorker

class PersistentQueueTests(unittest.TestCase):
    def test_claim_and_success(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = SQLiteJobQueue(Path(directory) / "jobs.db")
            job = queue.enqueue("sync", {"value": 7})
            output = []
            result = JobWorker(
                queue,
                {"sync": lambda payload: output.append(payload["value"])},
                "worker-1",
            ).run_once()
            self.assertTrue(result.processed)
            self.assertEqual(queue.get(job.job_id).status, "SUCCEEDED")
            self.assertEqual(output, [7])

    def test_dead_letter_after_max_attempts(self):
        with tempfile.TemporaryDirectory() as directory:
            queue = SQLiteJobQueue(Path(directory) / "jobs.db")
            job = queue.enqueue("fail", {}, max_attempts=2)
            worker = JobWorker(queue, {"fail": lambda payload: (_ for _ in ()).throw(RuntimeError("x"))}, "w1")
            worker.run_once()
            self.assertEqual(queue.get(job.job_id).status, "PENDING")
            worker.run_once()
            self.assertEqual(queue.get(job.job_id).status, "DEAD")

if __name__ == "__main__":
    unittest.main()
