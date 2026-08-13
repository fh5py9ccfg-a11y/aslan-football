import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.database import ProductionDatabase
from aslan_ozaslan.fixtures import FixtureRecord, FixtureRepository
from aslan_ozaslan.providers.results import ExternalResult, ResultSyncService
from aslan_ozaslan.results import ResultRepository

class FakeAdapter:
    name = "fake-results"
    def completed_results(self):
        return [
            ExternalResult("ext-1", 2, 1, "FINISHED"),
            ExternalResult("ext-2", 0, 0, "SCHEDULED"),
        ]

class ResultSyncTests(unittest.TestCase):
    def test_only_finished_and_mapped_results_are_saved(self):
        with tempfile.TemporaryDirectory() as directory:
            db = ProductionDatabase(Path(directory) / "app.db")
            FixtureRepository(db).upsert(FixtureRecord(
                "fx1","lig","2026","A","B","2026-08-01T20:00:00+00:00","SCHEDULED"
            ))
            count = ResultSyncService(
                FakeAdapter(), {"ext-1":"fx1"}, ResultRepository(db)
            ).sync()
            self.assertEqual(count, 1)

if __name__ == "__main__":
    unittest.main()
