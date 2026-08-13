import sys, unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.football import (
    League, Team, MatchResult, FootballRepository,
    TeamFormAnalyzer, MatchupAnalyzer,
)
from aslan_ozaslan.ratings_v5 import EloModel, EloRegistry, TeamRating
from aslan_ozaslan.admin.football_page import render_matchup_page

class FootballIntelligenceTests(unittest.TestCase):
    def test_repository_supports_multiple_leagues(self):
        repo = FootballRepository()
        repo.add_league(League("tr1","Süper Lig","TR","2026-27"))
        repo.add_league(League("eng1","Premier League","EN","2026-27"))
        repo.add_team(Team("a","tr1","A"))
        repo.add_team(Team("b","tr1","B"))
        repo.add_match(MatchResult(
            "m1","tr1","2026-27",
            datetime(2026,8,1,tzinfo=timezone.utc),"a","b",2,1
        ))
        self.assertEqual(len(repo.matches_for_league("tr1")), 1)
        self.assertEqual(len(repo.matches_for_league("eng1")), 0)

    def test_elo_registry(self):
        update = EloModel().update(1500,1500,2,0)
        self.assertGreater(update.home_after, 1500)
        home, away = EloRegistry().apply_result(
            home_team_id="a", away_team_id="b", home_goals=1, away_goals=1
        )
        self.assertEqual(home.matches_played, 1)
        self.assertEqual(away.matches_played, 1)

    def test_form_matchup_and_page(self):
        now = datetime(2026,8,10,tzinfo=timezone.utc)
        matches = [
            MatchResult("1","l","s",now,"a","b",2,0),
            MatchResult("2","l","s",now-timedelta(days=7),"c","a",1,1),
            MatchResult("3","l","s",now-timedelta(days=14),"a","d",3,1),
        ]
        analyzer = TeamFormAnalyzer()
        home_form = analyzer.analyze("a", matches)
        away_form = analyzer.analyze("b", [matches[0]])
        assessment = MatchupAnalyzer().assess(
            home_rating=TeamRating("a",1550,10),
            away_rating=TeamRating("b",1480,10),
            home_form=home_form,
            away_form=away_form,
        )
        self.assertEqual(home_form.points, 7)
        self.assertEqual(assessment.edge, "HOME")
        self.assertIn("Elo farkı", render_matchup_page(assessment))

if __name__ == "__main__":
    unittest.main()
