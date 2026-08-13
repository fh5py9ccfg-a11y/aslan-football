from __future__ import annotations
from dataclasses import dataclass
from .form import TeamFormSnapshot
from aslan_ozaslan.ratings_v5 import TeamRating

@dataclass(frozen=True)
class MatchupAssessment:
    home_team_id: str
    away_team_id: str
    home_strength: float
    away_strength: float
    edge: str
    confidence: float
    explanation: tuple[str, ...]

class MatchupAnalyzer:
    def assess(self, *, home_rating: TeamRating, away_rating: TeamRating,
               home_form: TeamFormSnapshot, away_form: TeamFormSnapshot):
        home_strength = home_rating.rating + home_form.points_per_match * 35 + 40
        away_strength = away_rating.rating + away_form.points_per_match * 35
        delta = home_strength - away_strength
        edge = "HOME" if delta > 20 else "AWAY" if delta < -20 else "BALANCED"
        return MatchupAssessment(
            home_rating.team_id, away_rating.team_id,
            home_strength, away_strength, edge,
            min(abs(delta) / 200.0, 1.0),
            (
                f"Elo farkı: {home_rating.rating-away_rating.rating:.1f}",
                f"Form puan ortalaması farkı: {home_form.points_per_match-away_form.points_per_match:.2f}",
                "Ev sahibi avantajı: +40.0",
            ),
        )
