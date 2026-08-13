import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.simulation_v5 import (
    MatchState,
    MatchSimulationInput,
    PoissonSampler,
    MatchEventSimulator,
    MonteCarloMatchSimulator,
    ScenarioComparator,
)
from aslan_ozaslan.admin.match_simulation_page import render_match_simulation_page

class MatchSimulationTests(unittest.TestCase):
    def item(self):
        return MatchSimulationInput(
            home_team_id="home",
            away_team_id="away",
            home_expected_goals=1.8,
            away_expected_goals=1.1,
            home_red_card_probability=0.04,
            away_red_card_probability=0.05,
        )

    def test_poisson_probability(self):
        sampler = PoissonSampler()
        self.assertAlmostEqual(sampler.probability(0, 0), 1.0)
        self.assertGreater(sampler.probability(1, 1.2), 0)

    def test_single_match_is_deterministic_with_seed(self):
        simulator = MatchEventSimulator()
        first = simulator.simulate(self.item(), seed=44)
        second = simulator.simulate(self.item(), seed=44)
        self.assertEqual(first, second)

    def test_monte_carlo_probabilities_sum_to_one(self):
        simulator = MonteCarloMatchSimulator()
        baseline = simulator.run(self.item(), iterations=1500, seed=10)
        self.assertAlmostEqual(
            baseline.home_win_probability
            + baseline.draw_probability
            + baseline.away_win_probability,
            1.0,
        )
        self.assertGreater(
            baseline.home_win_probability,
            baseline.away_win_probability,
        )

        scenario = simulator.run(
            self.item(),
            iterations=1500,
            seed=10,
            starting_state=MatchState(
                minute=70,
                home_goals=0,
                away_goals=1,
                home_red_cards=0,
                away_red_cards=0,
            ),
        )
        difference = ScenarioComparator().compare(baseline, scenario)
        self.assertLess(difference.home_win_change, 0)

        page = render_match_simulation_page(scenario, difference)
        self.assertIn("Monte Carlo Maç Simülasyonu", page)
        self.assertIn("Senaryo farkı", page)

if __name__ == "__main__":
    unittest.main()
