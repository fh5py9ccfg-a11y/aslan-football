import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.predictions import PredictionRecord
from aslan_ozaslan.results import MatchResult, SettlementEngine

class SettlementTests(unittest.TestCase):
    def test_settles_correct_prediction(self):
        prediction = PredictionRecord(
            "calc-1","fx-1","m1","OK",0.6,0.25,0.15,1.7,0.8,82,()
        )
        settled = SettlementEngine().settle(
            prediction,
            MatchResult("fx-1", 2, 0),
        )
        self.assertTrue(settled.correct)
        self.assertEqual(settled.actual_outcome, 0)

    def test_blocked_prediction_cannot_be_settled(self):
        prediction = PredictionRecord(
            "calc-2","fx-2","m1","BLOCKED",None,None,None,None,None,0,("Veri yok",)
        )
        with self.assertRaises(ValueError):
            SettlementEngine().settle(prediction, MatchResult("fx-2", 1, 0))

if __name__ == "__main__":
    unittest.main()
