import sys, unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.jobs import IntervalScheduler, JobQueue

class SchedulerTests(unittest.TestCase):
    def test_due_task_is_enqueued_once_per_interval(self):
        scheduler = IntervalScheduler()
        queue = JobQueue()
        now = datetime(2026, 7, 31, 8, 0, tzinfo=timezone.utc)
        scheduler.register(
            name="sync-results",
            interval_seconds=60,
            payload_factory=lambda: {"source":"primary"},
            start_at=now,
        )
        self.assertEqual(scheduler.enqueue_due(queue, now), 1)
        self.assertEqual(scheduler.enqueue_due(queue, now), 0)
        self.assertEqual(queue.list_jobs()[0].payload["source"], "primary")

if __name__ == "__main__":
    unittest.main()
