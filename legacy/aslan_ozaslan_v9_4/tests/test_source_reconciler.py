import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.reconciliation import CandidateValue, SourceReconciler


class SourceReconcilerTests(unittest.TestCase):
    def test_accepts_weighted_consensus(self):
        decision = SourceReconciler(minimum_support_weight=1.5).decide([
            CandidateValue("official", "postponed", 1.0, 100),
            CandidateValue("provider-b", "postponed", 0.8, 101),
            CandidateValue("provider-c", "scheduled", 0.4, 102),
        ])
        self.assertTrue(decision.accepted)
        self.assertEqual(decision.value, "postponed")
        self.assertIn("official", decision.supporting_providers)

    def test_rejects_weak_single_source(self):
        decision = SourceReconciler(minimum_support_weight=1.5).decide([
            CandidateValue("unknown", "scheduled", 0.5, 100),
        ])
        self.assertFalse(decision.accepted)
        self.assertIsNone(decision.value)


if __name__ == "__main__":
    unittest.main()
