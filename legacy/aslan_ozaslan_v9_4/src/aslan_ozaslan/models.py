from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class MatchInput:
    fixture_id: str
    competition_id: str
    season: str
    home_team_id: str
    away_team_id: str
    home_sample_count: int
    away_sample_count: int
    league_sample_count: int
    status: str = "scheduled"
    data_age_hours: float = 0.0
    home_strength: Optional[float] = None
    away_strength: Optional[float] = None
    draw_tendency: Optional[float] = None


@dataclass(frozen=True)
class PredictionResult:
    status: str
    fixture_id: str
    message: str
    home_probability: Optional[float] = None
    draw_probability: Optional[float] = None
    away_probability: Optional[float] = None
    data_confidence: int = 0
    model_version: str = "v1-foundation"
    calculation_id: Optional[str] = None
