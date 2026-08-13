import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.players_v5 import (
    Player,
    PlayerMatchPerformance,
    PositionNormalizer,
    PlayerValueCalculator,
    PlayerFormAnalyzer,
    SquadAvailability,
    SquadImpactAnalyzer,
)
from aslan_ozaslan.admin.player_analytics_page import render_player_analytics_page

class PlayerAnalyticsTests(unittest.TestCase):
    def performance(self, match_id, goals=0, assists=0, xg=0.2, xa=0.1):
        return PlayerMatchPerformance(
            player_id="p1",
            match_id=match_id,
            minutes=90,
            goals=goals,
            assists=assists,
            expected_goals=xg,
            expected_assists=xa,
            progressive_passes=8,
            key_passes=2,
            successful_dribbles=3,
            pressures=18,
            recoveries=7,
            interceptions=2,
            tackles_won=3,
            duels_won=6,
            duels_total=10,
        )

    def test_position_profile_and_value_score(self):
        profile = PositionNormalizer().build_profile(
            position="CM",
            metric_name="progressive_passes",
            values=[4,6,8,10],
        )
        value = PositionNormalizer().normalize(10, profile)
        self.assertGreater(value, 0)

        score = PlayerValueCalculator().calculate(
            self.performance("m1", goals=1, assists=1)
        )
        self.assertGreater(score.overall, 0)
        self.assertGreater(score.attacking, 0)
        self.assertGreater(score.creativity, 0)

    def test_form_trend_and_page(self):
        calculator = PlayerValueCalculator()
        scores = [
            calculator.calculate(self.performance("m1", goals=0)),
            calculator.calculate(self.performance("m2", goals=0, assists=1)),
            calculator.calculate(self.performance("m3", goals=1, assists=1)),
            calculator.calculate(self.performance("m4", goals=2, assists=1)),
        ]
        trend = PlayerFormAnalyzer().analyze("p1", scores, recent_window=2)
        self.assertEqual(trend.trend, "RISING")

        player = Player("p1","t1","Oyuncu Bir","CM",24)
        player.validate()
        page = render_player_analytics_page(player, scores[-1], trend)
        self.assertIn("Oyuncu Bir Oyuncu Analizi", page)
        self.assertIn("Form trendi", page)

    def test_squad_impact(self):
        calculator = PlayerValueCalculator()
        score1 = calculator.calculate(self.performance("m1", goals=1))
        score2 = score1.__class__(
            player_id="p2",
            attacking=score1.attacking,
            creativity=score1.creativity,
            progression=score1.progression,
            defensive=score1.defensive,
            pressing=score1.pressing,
            reliability=score1.reliability,
            overall=score1.overall,
        )
        report = SquadImpactAnalyzer().analyze(
            [score1, score2],
            [
                SquadAvailability("p1", True, 1.0),
                SquadAvailability("p2", False, 0.8),
            ],
        )
        self.assertLess(report.availability_ratio, 1.0)
        self.assertEqual(report.missing_player_ids, ("p2",))

if __name__ == "__main__":
    unittest.main()
