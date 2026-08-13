import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.jobs import SQLiteJobQueue, JobWorker
from aslan_ozaslan.metrics import MetricsRegistry
from aslan_ozaslan.admin import DeadLetterRepository

class MetricsDeadLetterTests(unittest.TestCase):
    def test_metrics_snapshot(self):
        registry = MetricsRegistry()
        registry.counter("jobs_processed").increment(2)
        registry.gauge("queue_depth").set(4)
        self.assertEqual(registry.snapshot()["jobs_processed"], 2)
        self.assertEqual(registry.snapshot()["queue_depth"], 4.0)

    def test_dead_letter_list(self):
        with tempfile.TemporaryDirectory() as directory:
            db = Path(directory) / "jobs.db"
            queue = SQLiteJobQueue(db)
            queue.enqueue("fail", {}, max_attempts=1)
            JobWorker(
                queue,
                {"fail": lambda payload: (_ for _ in ()).throw(RuntimeError("boom"))},
                "worker-1",
            ).run_once()
            rows = DeadLetterRepository(str(db)).list()
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].error, "boom")

if __name__ == "__main__":
    unittest.main()
