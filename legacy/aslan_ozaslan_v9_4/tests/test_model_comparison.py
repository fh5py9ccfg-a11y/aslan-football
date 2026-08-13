import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.comparison import ModelCandidate, compare_models

class ModelComparisonTests(unittest.TestCase):
    def test_log_loss_has_priority(self):
        result = compare_models([
            ModelCandidate("A", 0.60, 0.20, 0.95, 0.04),
            ModelCandidate("B", 0.58, 0.19, 0.85, 0.05),
        ])
        self.assertEqual(result.champion, "B")

    def test_empty_candidates_are_rejected(self):
        with self.assertRaises(ValueError):
            compare_models([])

if __name__ == "__main__":
    unittest.main()
