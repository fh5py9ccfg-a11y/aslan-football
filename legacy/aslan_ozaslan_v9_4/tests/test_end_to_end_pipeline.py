import sys, unittest
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.league_config import LeagueParameters, LeagueParameterRegistry
from aslan_ozaslan.market import OddsSnapshot
from aslan_ozaslan.models_core import TeamStrengthInput
from aslan_ozaslan.pipeline import AnalysisInput, EndToEndAnalysisPipeline
from aslan_ozaslan.squad import PlayerAvailability

class EndToEndPipelineTests(unittest.TestCase):
    def setUp(self):
        registry = LeagueParameterRegistry()
        registry.register(LeagueParameters("lig", 1.35, 1.10, 20, 6))
        self.pipeline = EndToEndAnalysisPipeline(registry)

    def base_input(self, **changes):
        payload = dict(
            fixture_id="fx-1",
            competition_id="lig",
            kickoff_at=datetime(2026,8,1,tzinfo=timezone.utc),
            home_team_id="A",
            away_team_id="B",
            home_strength=TeamStrengthInput(1.2,0.9,2.1,1550),
            away_strength=TeamStrengthInput(1.0,1.0,1.4,1500),
            home_players=(),
            away_players=(),
            odds=OddsSnapshot(
                datetime(2026,7,30,tzinfo=timezone.utc),2.0,3.4,3.8,"book-a"),
            data_quality_score=85,
        )
        payload.update(changes)
        return AnalysisInput(**payload)

    def test_full_pipeline_returns_probabilities(self):
        result = self.pipeline.analyze(self.base_input())
        self.assertEqual(result.status, "OK")
        self.assertAlmostEqual(
            result.home_probability + result.draw_probability + result.away_probability,
            1.0, places=6)
        self.assertIsNotNone(result.explanation)
        self.assertGreater(result.data_confidence, 0)

    def test_low_quality_blocks_prediction(self):
        result = self.pipeline.analyze(self.base_input(data_quality_score=40))
        self.assertEqual(result.status, "BLOCKED")
        self.assertIsNone(result.home_probability)

    def test_stale_data_blocks_prediction(self):
        result = self.pipeline.analyze(self.base_input(stale_data=True))
        self.assertEqual(result.status, "BLOCKED")

    def test_squad_absence_changes_output(self):
        normal = self.pipeline.analyze(self.base_input())
        impacted = self.pipeline.analyze(
            self.base_input(
                home_players=(
                    PlayerAvailability("p1",1.0,0.25,0.05,"OUT"),
                )
            )
        )
        self.assertNotEqual(normal.home_expected_goals, impacted.home_expected_goals)

if __name__ == "__main__":
    unittest.main()
