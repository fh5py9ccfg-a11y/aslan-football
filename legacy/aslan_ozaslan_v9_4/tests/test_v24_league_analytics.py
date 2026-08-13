import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.analytics import LeaguePerformanceCalculator
from aslan_ozaslan.results import SettledPrediction

class LeagueAnalyticsTests(unittest.TestCase):
    def test_league_accuracy(self):
        rows = [
            SettledPrediction("c1","f1",0,0,True,80,"m1"),
            SettledPrediction("c2","f2",2,1,False,60,"m1"),
        ]
        report = LeaguePerformanceCalculator().calculate("super-lig", rows)
        self.assertEqual(report.accuracy, 0.5)
        self.assertEqual(report.average_confidence, 70.0)

if __name__ == "__main__":
    unittest.main()
