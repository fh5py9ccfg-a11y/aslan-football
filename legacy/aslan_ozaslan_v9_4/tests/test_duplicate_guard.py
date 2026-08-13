import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.reporting import DuplicateProbabilityGuard

class DuplicateGuardTests(unittest.TestCase):
    def test_three_identical_distributions_trigger_alert(self):
        result = DuplicateProbabilityGuard(threshold=3).inspect([
            ("a",0.44,0.26,0.30),
            ("b",0.44,0.26,0.30),
            ("c",0.44,0.26,0.30),
        ])
        self.assertTrue(result.triggered)
        self.assertEqual(len(result.fixture_ids),3)

    def test_distinct_distributions_do_not_trigger(self):
        result = DuplicateProbabilityGuard().inspect([
            ("a",0.44,0.26,0.30),
            ("b",0.40,0.30,0.30),
            ("c",0.50,0.20,0.30),
        ])
        self.assertFalse(result.triggered)

if __name__ == "__main__":
    unittest.main()
