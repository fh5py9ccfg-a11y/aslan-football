import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.domain import FixtureRecord, TeamSnapshot
from aslan_ozaslan.validation import DataQualityGate

class DataQualityGateTests(unittest.TestCase):
    def setUp(self):
        self.now = datetime(2026, 7, 30, 12, 0, tzinfo=timezone.utc)
        self.fixture = FixtureRecord(
            fixture_id="fx", provider="p", competition_id="c", season="2026",
            kickoff_at=self.now + timedelta(days=1), home_team_id="h", away_team_id="a",
            status="SCHEDULED", observed_at=self.now,
        )

    def snapshot(self, team_id, **overrides):
        values = dict(
            provider="p", team_id=team_id, competition_id="c", observed_at=self.now,
            matches_played=10, goals_for=15, goals_against=10,
            home_matches=5, away_matches=5, injuries_known=True, lineup_known=True,
        )
        values.update(overrides)
        return TeamSnapshot(**values)

    def test_good_data_is_accepted(self):
        result = DataQualityGate().evaluate(
            fixture=self.fixture, home=self.snapshot("h"), away=self.snapshot("a"), now=self.now
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.score, 100)

    def test_stale_data_is_blocked(self):
        result = DataQualityGate(max_snapshot_age_hours=24).evaluate(
            fixture=self.fixture,
            home=self.snapshot("h", observed_at=self.now - timedelta(hours=30)),
            away=self.snapshot("a"), now=self.now,
        )
        self.assertFalse(result.accepted)
        self.assertIn("Takım verisi güncel değil", result.reasons)

    def test_missing_lineup_lowers_score_without_blocking(self):
        result = DataQualityGate().evaluate(
            fixture=self.fixture,
            home=self.snapshot("h", lineup_known=False),
            away=self.snapshot("a"), now=self.now,
        )
        self.assertTrue(result.accepted)
        self.assertEqual(result.score, 90)

if __name__ == "__main__":
    unittest.main()
