import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.predictions import PredictionRecord
from aslan_ozaslan.webapp.result_view import render_prediction_result

class ResultViewTests(unittest.TestCase):
    def test_blocked_hides_percentages(self):
        html = render_prediction_result(PredictionRecord(
            "c","f","m","BLOCKED",None,None,None,None,None,0,("Veri yok",)
        ))
        self.assertIn("Analiz çalıştırılmadı", html)
        self.assertNotIn("%", html)

if __name__ == "__main__":
    unittest.main()
