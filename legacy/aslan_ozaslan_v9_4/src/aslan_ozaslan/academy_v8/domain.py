from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class AcademyPlayer:
    player_id: str
    name: str
    position: str
    age: int
    current_level: float
    potential_level: float
    training_attendance: float
    match_minutes_share: float
    physical_readiness: float
    tactical_readiness: float
    psychological_readiness: float
    injury_risk: float
    discipline_score: float

    def validate(self) -> None:
        if not all(value.strip() for value in (
            self.player_id, self.name, self.position
        )):
            raise ValueError("Akademi oyuncusu alanları boş olamaz")
        if not 14 <= self.age <= 23:
            raise ValueError("Akademi oyuncusu yaşı geçersiz")
        for value in (
            self.current_level,
            self.potential_level,
            self.training_attendance,
            self.match_minutes_share,
            self.physical_readiness,
            self.tactical_readiness,
            self.psychological_readiness,
            self.injury_risk,
            self.discipline_score,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Akademi metrikleri 0 ile 1 arasında olmalıdır")

@dataclass(frozen=True)
class AcademyAssessment:
    player_id: str
    development_score: float
    first_team_readiness: float
    loan_suitability: float
    projected_level_12m: float
    projected_market_value_24m: float
    pathway: str
    risks: tuple[str, ...]
