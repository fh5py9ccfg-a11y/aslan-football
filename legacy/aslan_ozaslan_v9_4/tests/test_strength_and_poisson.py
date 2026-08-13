import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.models_core import (
    TeamStrengthInput, ExpectedGoalsEstimator, PoissonScoreModel
)

class StrengthAndPoissonTests(unittest.TestCase):
    def test_home_advantage_affects_xg(self):
        estimator = ExpectedGoalsEstimator(league_goal_average=1.3, home_advantage_multiplier=1.12)
        home = TeamStrengthInput(1.1, 0.9, 2.0, 1550)
        away = TeamStrengthInput(1.0, 1.0, 1.5, 1500)
        home_xg, away_xg = estimator.estimate(home, away)
        self.assertGreater(home_xg, away_xg)

    def test_probabilities_sum_to_one(self):
        distribution = PoissonScoreModel(max_goals=8).predict(1.6, 1.1)
        self.assertAlmostEqual(
            distribution.home_win + distribution.draw + distribution.away_win,
            1.0,
            places=6,
        )

    def test_different_xg_produce_different_results(self):
        model = PoissonScoreModel()
        first = model.predict(1.8, 0.8)
        second = model.predict(0.9, 1.5)
        self.assertNotEqual(
            (first.home_win, first.draw, first.away_win),
            (second.home_win, second.draw, second.away_win),
        )

    def test_scorelines_are_sorted(self):
        result = PoissonScoreModel().predict(1.4, 1.0)
        probabilities = [row[2] for row in result.scorelines[:10]]
        self.assertEqual(probabilities, sorted(probabilities, reverse=True))

if __name__ == "__main__":
    unittest.main()
