import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import (
    ServiceLevelObjective,
    SLOEvaluator,
    Runbook,
    RunbookRegistry,
)

class SloRunbookTests(unittest.TestCase):
    def test_slo_evaluation(self):
        result = SLOEvaluator().evaluate(
            ServiceLevelObjective("availability", 0.999, 30),
            0.9995,
        )
        self.assertTrue(result.met)
        self.assertGreater(result.error_budget_remaining, 0)

    def test_runbook_registry(self):
        registry = RunbookRegistry()
        registry.register(Runbook(
            "provider_down",
            "Provider outage",
            ("confirm-impact", "switch-provider", "monitor"),
        ))
        self.assertEqual(
            registry.get("provider_down").title,
            "Provider outage",
        )

if __name__ == "__main__":
    unittest.main()
