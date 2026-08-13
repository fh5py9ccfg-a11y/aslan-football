import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan import MatchInput, PredictionEngine


class PredictionEngineTests(unittest.TestCase):
    def setUp(self):
        self.engine = PredictionEngine()

    def test_no_prediction_when_team_data_is_missing(self):
        match = MatchInput(
            fixture_id="match-1",
            competition_id="league-1",
            season="2026",
            home_team_id="home-a",
            away_team_id="away-a",
            home_sample_count=0,
            away_sample_count=0,
            league_sample_count=0,
        )
        result = self.engine.predict(match)
        self.assertEqual(result.status, "INSUFFICIENT_DATA")
        self.assertIsNone(result.home_probability)
        self.assertEqual(result.data_confidence, 0)

    def test_different_matches_use_different_cache_keys(self):
        base = dict(
            competition_id="league-1",
            season="2026",
            home_team_id="home-a",
            away_team_id="away-a",
            home_sample_count=10,
            away_sample_count=10,
            league_sample_count=50,
            home_strength=1.5,
            away_strength=1.0,
            draw_tendency=0.8,
        )
        first = MatchInput(fixture_id="match-1", **base)
        second = MatchInput(fixture_id="match-2", **base)
        self.assertNotEqual(self.engine.cache_key(first), self.engine.cache_key(second))

    def test_match_specific_inputs_produce_match_specific_probabilities(self):
        first = MatchInput(
            fixture_id="match-1",
            competition_id="league-1",
            season="2026",
            home_team_id="home-a",
            away_team_id="away-a",
            home_sample_count=10,
            away_sample_count=10,
            league_sample_count=50,
            home_strength=1.8,
            away_strength=0.8,
            draw_tendency=0.7,
        )
        second = MatchInput(
            fixture_id="match-2",
            competition_id="league-1",
            season="2026",
            home_team_id="home-b",
            away_team_id="away-b",
            home_sample_count=10,
            away_sample_count=10,
            league_sample_count=50,
            home_strength=1.0,
            away_strength=1.5,
            draw_tendency=0.9,
        )
        first_result = self.engine.predict(first)
        second_result = self.engine.predict(second)
        self.assertNotEqual(
            (first_result.home_probability, first_result.draw_probability, first_result.away_probability),
            (second_result.home_probability, second_result.draw_probability, second_result.away_probability),
        )

    def test_probabilities_sum_to_one(self):
        match = MatchInput(
            fixture_id="match-3",
            competition_id="league-1",
            season="2026",
            home_team_id="home-c",
            away_team_id="away-c",
            home_sample_count=12,
            away_sample_count=11,
            league_sample_count=60,
            home_strength=1.3,
            away_strength=1.1,
            draw_tendency=0.75,
        )
        result = self.engine.predict(match)
        self.assertEqual(result.status, "OK")
        self.assertAlmostEqual(
            result.home_probability + result.draw_probability + result.away_probability,
            1.0,
            places=4,
        )

    def test_stale_data_blocks_prediction(self):
        match = MatchInput(
            fixture_id="stale-1", competition_id="league-1", season="2026",
            home_team_id="h", away_team_id="a", home_sample_count=10,
            away_sample_count=10, league_sample_count=50, data_age_hours=48,
            home_strength=1.4, away_strength=1.0, draw_tendency=0.8,
        )
        result = self.engine.predict(match)
        self.assertEqual(result.status, "INSUFFICIENT_DATA")
        self.assertIn("güncel değil", result.message)

    def test_postponed_match_blocks_prediction(self):
        match = MatchInput(
            fixture_id="postponed-1", competition_id="league-1", season="2026",
            home_team_id="h", away_team_id="a", home_sample_count=10,
            away_sample_count=10, league_sample_count=50, status="postponed",
            home_strength=1.4, away_strength=1.0, draw_tendency=0.8,
        )
        result = self.engine.predict(match)
        self.assertEqual(result.status, "INSUFFICIENT_DATA")

    def test_same_team_ids_are_rejected(self):
        match = MatchInput(
            fixture_id="bad-1", competition_id="league-1", season="2026",
            home_team_id="same", away_team_id="same", home_sample_count=10,
            away_sample_count=10, league_sample_count=50,
            home_strength=1.4, away_strength=1.0, draw_tendency=0.8,
        )
        with self.assertRaises(ValueError):
            self.engine.predict(match)

    def test_calculation_ids_are_fixture_scoped(self):
        common = dict(competition_id="league-1", season="2026", home_team_id="h",
                      away_team_id="a", home_sample_count=10, away_sample_count=10,
                      league_sample_count=50, home_strength=1.4, away_strength=1.0,
                      draw_tendency=0.8)
        a = MatchInput(fixture_id="id-a", **common)
        b = MatchInput(fixture_id="id-b", **common)
        self.assertNotEqual(self.engine.calculation_id(a), self.engine.calculation_id(b))


if __name__ == "__main__":
    unittest.main()
