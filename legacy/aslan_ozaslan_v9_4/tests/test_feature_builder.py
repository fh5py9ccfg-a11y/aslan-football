import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.features import HistoricalMatch, FeatureBuilder

class FeatureBuilderTests(unittest.TestCase):
    def test_future_data_is_ignored(self):
        kickoff = datetime(2026,8,1,tzinfo=timezone.utc)
        history = [
            HistoricalMatch("h1","lig",kickoff-timedelta(days=10),"A","C",2,0),
            HistoricalMatch("h2","lig",kickoff-timedelta(days=8),"B","D",1,1),
            HistoricalMatch("future","lig",kickoff+timedelta(days=1),"A","B",9,9),
        ]
        v = FeatureBuilder().build(
            fixture_id="target", competition_id="lig", kickoff_at=kickoff,
            home_team_id="A", away_team_id="B", history=history)
        self.assertEqual(v.home_goals_for, 2.0)
        self.assertEqual(v.away_goals_for, 1.0)

    def test_both_teams_need_history(self):
        kickoff = datetime(2026,8,1,tzinfo=timezone.utc)
        history = [HistoricalMatch("h1","lig",kickoff-timedelta(days=10),"A","C",2,0)]
        with self.assertRaises(ValueError):
            FeatureBuilder().build(
                fixture_id="target", competition_id="lig", kickoff_at=kickoff,
                home_team_id="A", away_team_id="B", history=history)

if __name__ == "__main__":
    unittest.main()
