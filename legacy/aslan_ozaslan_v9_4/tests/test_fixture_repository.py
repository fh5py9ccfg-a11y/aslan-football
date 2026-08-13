import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.database import ProductionDatabase
from aslan_ozaslan.fixtures import FixtureRecord, FixtureRepository

class FixtureRepositoryTests(unittest.TestCase):
    def test_upsert_and_list(self):
        with tempfile.TemporaryDirectory() as directory:
            db = ProductionDatabase(Path(directory) / "app.db")
            repo = FixtureRepository(db)
            repo.upsert(FixtureRecord(
                "fx-1","lig","2026","A","B","2026-08-01T20:00:00+00:00","SCHEDULED"
            ))
            rows = repo.upcoming()
            self.assertEqual(rows[0].fixture_id, "fx-1")

if __name__ == "__main__":
    unittest.main()
