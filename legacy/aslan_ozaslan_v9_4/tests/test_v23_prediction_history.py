import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.database import ProductionDatabase
from aslan_ozaslan.fixtures import FixtureRecord, FixtureRepository
from aslan_ozaslan.predictions import PredictionRecord, PredictionRepository, ScorecardCalculator

class PredictionHistoryTests(unittest.TestCase):
    def test_repository_and_scorecard(self):
        with tempfile.TemporaryDirectory() as directory:
            db = ProductionDatabase(Path(directory)/"app.db")
            FixtureRepository(db).upsert(FixtureRecord(
                "fx","lig","2026","A","B","2026-08-01T20:00:00+00:00","SCHEDULED"
            ))
            repo = PredictionRepository(db)
            repo.insert(PredictionRecord(
                "calc","fx","m1","OK",0.5,0.3,0.2,1.4,1.0,80,()
            ))
            self.assertEqual(repo.latest_for_fixture("fx").calculation_id,"calc")
            score = ScorecardCalculator().calculate([((0.5,0.3,0.2),0,80)])
            self.assertEqual(score.accuracy,1.0)

if __name__ == "__main__":
    unittest.main()
