import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.scheduling import Job, JobRunner, JobStatus

class JobRunnerTests(unittest.TestCase):
    def test_successful_job_is_recorded(self):
        completed, result = JobRunner().run(Job.create("fixture:1"), lambda: 42)
        self.assertEqual(completed.status, JobStatus.SUCCEEDED)
        self.assertEqual(result, 42)

    def test_failed_job_is_recorded_without_fake_result(self):
        failed, result = JobRunner().run(
            Job.create("fixture:2"),
            lambda: (_ for _ in ()).throw(RuntimeError("boom")),
        )
        self.assertEqual(failed.status, JobStatus.FAILED)
        self.assertIsNone(result)
        self.assertEqual(failed.error, "boom")

if __name__ == "__main__": unittest.main()
