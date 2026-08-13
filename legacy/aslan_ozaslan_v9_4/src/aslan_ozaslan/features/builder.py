from dataclasses import dataclass
from datetime import datetime
from statistics import mean

@dataclass(frozen=True)
class HistoricalMatch:
    fixture_id: str
    competition_id: str
    kickoff_at: datetime
    home_team_id: str
    away_team_id: str
    home_goals: int
    away_goals: int

@dataclass(frozen=True)
class FeatureVector:
    fixture_id: str
    home_form_points: float
    away_form_points: float
    home_goals_for: float
    away_goals_for: float
    home_goals_against: float
    away_goals_against: float
    sample_cutoff_at: datetime

class FeatureBuilder:
    def __init__(self, form_window: int = 5):
        if form_window <= 0:
            raise ValueError("form_window pozitif olmalıdır")
        self.form_window = form_window

    def build(self, *, fixture_id, competition_id, kickoff_at, home_team_id, away_team_id, history):
        eligible = [m for m in history if m.competition_id == competition_id and m.kickoff_at < kickoff_at]
        home_rows = self._team_rows(home_team_id, eligible)[-self.form_window:]
        away_rows = self._team_rows(away_team_id, eligible)[-self.form_window:]
        if not home_rows or not away_rows:
            raise ValueError("Özellik üretmek için yeterli geçmiş maç yok")
        return FeatureVector(
            fixture_id=fixture_id,
            home_form_points=round(mean(r[0] for r in home_rows), 4),
            away_form_points=round(mean(r[0] for r in away_rows), 4),
            home_goals_for=round(mean(r[1] for r in home_rows), 4),
            away_goals_for=round(mean(r[1] for r in away_rows), 4),
            home_goals_against=round(mean(r[2] for r in home_rows), 4),
            away_goals_against=round(mean(r[2] for r in away_rows), 4),
            sample_cutoff_at=kickoff_at,
        )

    def _team_rows(self, team_id, history):
        rows = []
        for match in sorted(history, key=lambda m: m.kickoff_at):
            if team_id == match.home_team_id:
                gf, ga = match.home_goals, match.away_goals
            elif team_id == match.away_team_id:
                gf, ga = match.away_goals, match.home_goals
            else:
                continue
            points = 3 if gf > ga else 1 if gf == ga else 0
            rows.append((points, gf, ga))
        return rows
