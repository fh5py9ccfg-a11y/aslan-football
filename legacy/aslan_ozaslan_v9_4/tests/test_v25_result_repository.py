import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.database import ProductionDatabase
from aslan_ozaslan.fixtures import FixtureRecord, FixtureRepository
from aslan_ozaslan.predictions import PredictionRecord, PredictionRepository
from aslan_ozaslan.results import ResultRepository, StoredMatchResult, StoredSettlement

class ResultRepositoryTests(unittest.TestCase):
    def test_persists_result_and_settlement(self):
        with tempfile.TemporaryDirectory() as directory:
            db = ProductionDatabase(Path(directory) / "app.db")
            FixtureRepository(db).upsert(FixtureRecord(
                "fx1","lig","2026","A","B","2026-08-01T20:00:00+00:00","SCHEDULED"
            ))
            PredictionRepository(db).insert(PredictionRecord(
                "c1","fx1","m1","OK",0.6,0.2,0.2,1.8,0.9,81,()
            ))
            repo = ResultRepository(db)
            repo.upsert_result(StoredMatchResult("fx1",2,0,"provider-a"))
            repo.save_settlement(StoredSettlement(
                "c1","fx1",0,0,True,81,"m1","lig"
            ))
            rows = repo.league_rows("lig")
            self.assertEqual(len(rows), 1)
            self.assertTrue(rows[0].correct)

if __name__ == "__main__":
    unittest.main()
