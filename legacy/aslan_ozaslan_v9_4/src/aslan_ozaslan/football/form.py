from __future__ import annotations
from dataclasses import dataclass
from .domain import MatchResult

@dataclass(frozen=True)
class TeamFormSnapshot:
    team_id: str
    matches: int
    wins: int
    draws: int
    losses: int
    goals_for: int
    goals_against: int
    points: int
    points_per_match: float
    goal_difference: int

class TeamFormAnalyzer:
    def analyze(self, team_id: str, matches: list[MatchResult], limit: int = 5):
        if limit <= 0:
            raise ValueError("limit pozitif olmalıdır")
        selected = sorted(matches, key=lambda m: m.played_at, reverse=True)[:limit]
        wins = draws = losses = gf = ga = 0
        for match in selected:
            if team_id == match.home_team_id:
                scored, conceded = match.home_goals, match.away_goals
            elif team_id == match.away_team_id:
                scored, conceded = match.away_goals, match.home_goals
            else:
                raise ValueError("Takım maç içinde bulunmuyor")
            gf += scored
            ga += conceded
            if scored > conceded: wins += 1
            elif scored == conceded: draws += 1
            else: losses += 1
        played = len(selected)
        points = wins * 3 + draws
        return TeamFormSnapshot(
            team_id, played, wins, draws, losses, gf, ga, points,
            points / played if played else 0.0, gf - ga,
        )
