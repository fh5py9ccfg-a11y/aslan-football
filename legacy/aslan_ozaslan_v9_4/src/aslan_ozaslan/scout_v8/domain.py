from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PlayerDNA:
    player_id: str
    passing: float
    progression: float
    dribbling: float
    pressing: float
    defending: float
    aerial: float
    finishing: float
    creativity: float
    athleticism: float
    consistency: float

    def validate(self) -> None:
        if not self.player_id.strip():
            raise ValueError("player_id boş olamaz")
        values = (
            self.passing,
            self.progression,
            self.dribbling,
            self.pressing,
            self.defending,
            self.aerial,
            self.finishing,
            self.creativity,
            self.athleticism,
            self.consistency,
        )
        if any(value < 0 or value > 1 for value in values):
            raise ValueError("DNA metrikleri 0 ile 1 arasında olmalıdır")

@dataclass(frozen=True)
class ScoutCandidate:
    player_id: str
    age: int
    current_level: float
    potential_level: float
    market_value: float
    annual_salary: float
    injury_risk: float
    adaptation_risk: float
    discipline_risk: float
    source_league_strength: float
    target_league_strength: float

    def validate(self) -> None:
        if not self.player_id.strip():
            raise ValueError("player_id boş olamaz")
        if not 15 <= self.age <= 45:
            raise ValueError("age geçersiz")
        for value in (
            self.current_level,
            self.potential_level,
            self.injury_risk,
            self.adaptation_risk,
            self.discipline_risk,
            self.source_league_strength,
            self.target_league_strength,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Scout skoru 0 ile 1 arasında olmalıdır")
        if self.market_value < 0 or self.annual_salary < 0:
            raise ValueError("Ekonomik değerler negatif olamaz")

@dataclass(frozen=True)
class ScoutAssessment:
    player_id: str
    club_fit_score: float
    projected_level_12m: float
    projected_level_24m: float
    league_translation_score: float
    hidden_gem_score: float
    risk_score: float
    recommendation: str
    reasons: tuple[str, ...]
