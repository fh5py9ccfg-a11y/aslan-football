import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import (
    RunbookHistory,
    SQLiteRunbookExecutionRepository,
)

class RunbookRepositoryTests(unittest.TestCase):
    def test_persistent_runbook_history(self):
        with tempfile.TemporaryDirectory() as directory:
            history = RunbookHistory()
            execution = history.start("exec-1", "provider_down", "ops")
            execution = history.record_step("exec-1", "confirm-impact")
            execution = history.finish("exec-1", "SUCCEEDED")

            repository = SQLiteRunbookExecutionRepository(
                Path(directory) / "runbooks.db"
            )
            repository.save(execution)
            loaded = repository.get("exec-1")
            self.assertEqual(loaded.status, "SUCCEEDED")
            self.assertEqual(loaded.completed_steps, ("confirm-impact",))

if __name__ == "__main__":
    unittest.main()
