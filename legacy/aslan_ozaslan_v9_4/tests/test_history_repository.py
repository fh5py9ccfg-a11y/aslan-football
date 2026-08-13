import sys, tempfile, unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.domain import FixtureRecord, TeamSnapshot
from aslan_ozaslan.storage import SQLiteHistoryRepository

class HistoryRepositoryTests(unittest.TestCase):
    def test_fixture_and_snapshot_persistence(self):
        now = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteHistoryRepository(Path(directory) / "history.db")
            fixture = FixtureRecord(
                fixture_id="fx-1", provider="p", competition_id="c", season="2026",
                kickoff_at=now, home_team_id="h", away_team_id="a",
                status="SCHEDULED", observed_at=now,
            )
            repository.upsert_fixture(fixture)
            snapshot = TeamSnapshot(
                provider="p", team_id="h", competition_id="c", observed_at=now,
                matches_played=10, goals_for=18, goals_against=9,
                home_matches=5, away_matches=5, injuries_known=True, lineup_known=False,
            )
            repository.add_team_snapshot(snapshot)
            loaded = repository.latest_team_snapshot(provider="p", team_id="h", competition_id="c")
            self.assertEqual(loaded.goals_for, 18)
            self.assertFalse(loaded.lineup_known)

    def test_invalid_snapshot_is_rejected(self):
        now = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)
        with tempfile.TemporaryDirectory() as directory:
            repository = SQLiteHistoryRepository(Path(directory) / "history.db")
            with self.assertRaises(ValueError):
                repository.add_team_snapshot(TeamSnapshot(
                    provider="p", team_id="h", competition_id="c", observed_at=now,
                    matches_played=3, goals_for=1, goals_against=1,
                    home_matches=2, away_matches=2, injuries_known=True, lineup_known=True,
                ))

if __name__ == "__main__":
    unittest.main()
