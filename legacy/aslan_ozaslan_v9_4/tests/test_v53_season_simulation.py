import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.football import ScheduledFixture, MonteCarloSeasonSimulator
from aslan_ozaslan.admin.season_projection_page import render_season_projection_page

class SeasonSimulationTests(unittest.TestCase):
    def test_deterministic_seed_and_probabilities(self):
        projections = MonteCarloSeasonSimulator().simulate(
            team_ids=["a","b","c","d"],
            fixtures=[
                ScheduledFixture("a","b",0.70,0.20,0.10),
                ScheduledFixture("c","d",0.40,0.30,0.30),
                ScheduledFixture("a","c",0.60,0.25,0.15),
                ScheduledFixture("b","d",0.45,0.30,0.25),
            ],
            existing_points={"a":50,"b":45,"c":42,"d":30},
            iterations=500,
            relegation_places=1,
            seed=42,
        )
        self.assertEqual(len(projections),4)
        self.assertAlmostEqual(
            sum(item.title_probability for item in projections),1.0
        )
        self.assertAlmostEqual(
            sum(item.relegation_probability for item in projections),1.0
        )
        page = render_season_projection_page(projections)
        self.assertIn("Monte Carlo Sezon Projeksiyonu", page)
        self.assertIn("Şampiyonluk", page)

if __name__ == "__main__":
    unittest.main()
