import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.monitoring import DistributionGuard

class DistributionGuardTests(unittest.TestCase):
    def test_three_distinct_matches_with_same_distribution_trigger_incident(self):
        guard = DistributionGuard(repeat_threshold=3)
        self.assertIsNone(guard.observe("a", .44, .26, .30))
        self.assertIsNone(guard.observe("b", .44, .26, .30))
        incident = guard.observe("c", .44, .26, .30)
        self.assertIsNotNone(incident)
        self.assertEqual(incident.fixture_ids, ("a", "b", "c"))

    def test_same_fixture_repeated_does_not_create_false_incident(self):
        guard = DistributionGuard(repeat_threshold=3)
        guard.observe("a", .44, .26, .30)
        guard.observe("a", .44, .26, .30)
        self.assertIsNone(guard.observe("b", .44, .26, .30))

if __name__ == "__main__": unittest.main()
