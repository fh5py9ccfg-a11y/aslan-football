import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import (
    SLOMeasurement,
    SLOMeasurementService,
    RunbookHistory,
)

class FakeSource:
    name = "metrics"
    def measure(self, objective_name, window_days):
        return SLOMeasurement(objective_name, 0.999, window_days, self.name)

class SloRunbookHistoryTests(unittest.TestCase):
    def test_slo_adapter(self):
        result = SLOMeasurementService(FakeSource()).collect("availability", 30)
        self.assertEqual(result.achieved, 0.999)

    def test_runbook_history(self):
        history = RunbookHistory()
        history.start("exec-1", "provider_down", "ops")
        history.record_step("exec-1", "confirm-impact")
        finished = history.finish("exec-1", "SUCCEEDED")
        self.assertEqual(finished.status, "SUCCEEDED")
        self.assertEqual(finished.completed_steps, ("confirm-impact",))

if __name__ == "__main__":
    unittest.main()
