import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan import MatchInput, PredictionEngine
from aslan_ozaslan.adapters import InMemoryDataProvider
from aslan_ozaslan.services import AnalysisPipeline
from aslan_ozaslan.storage import SQLiteAuditRepository

class PipelineAndAuditTests(unittest.TestCase):
    def test_pipeline_persists_audit_event(self):
        match = MatchInput(
            fixture_id="fixture-101", competition_id="league-1", season="2026",
            home_team_id="home-1", away_team_id="away-1",
            home_sample_count=10, away_sample_count=10, league_sample_count=50,
            home_strength=1.4, away_strength=1.0, draw_tendency=0.8,
        )
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteAuditRepository(Path(directory) / "audit.db")
            pipeline = AnalysisPipeline(
                provider=InMemoryDataProvider({match.fixture_id: match}),
                engine=PredictionEngine(), audit_repository=repo,
            )
            result = pipeline.analyze(match.fixture_id)
            events = repo.list_for_fixture(match.fixture_id)
            self.assertEqual(result.status, "OK")
            self.assertEqual(len(events), 1)
            self.assertIn("cache_key", events[0].payload)

    def test_insufficient_data_is_audited(self):
        match = MatchInput(
            fixture_id="fixture-102", competition_id="league-1", season="2026",
            home_team_id="home-2", away_team_id="away-2",
            home_sample_count=0, away_sample_count=0, league_sample_count=0,
        )
        with tempfile.TemporaryDirectory() as directory:
            repo = SQLiteAuditRepository(Path(directory) / "audit.db")
            pipeline = AnalysisPipeline(
                provider=InMemoryDataProvider({match.fixture_id: match}),
                engine=PredictionEngine(), audit_repository=repo,
            )
            result = pipeline.analyze(match.fixture_id)
            self.assertEqual(result.status, "INSUFFICIENT_DATA")
            self.assertEqual(repo.list_for_fixture(match.fixture_id)[0].status, "INSUFFICIENT_DATA")

if __name__ == "__main__":
    unittest.main()
