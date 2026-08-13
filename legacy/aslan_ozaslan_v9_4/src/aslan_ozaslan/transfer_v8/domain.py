from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TransferPlayerProfile:
    player_id: str
    name: str
    position: str
    age: int
    current_value_score: float
    form_trend: float
    injury_days_last_365: int
    minutes_last_365: int
    annual_salary: float
    estimated_fee: float
    contract_months_remaining: int
    league_strength: float

    def validate(self) -> None:
        if not all(value.strip() for value in (
            self.player_id, self.name, self.position
        )):
            raise ValueError("Oyuncu alanları boş olamaz")
        if not 15 <= self.age <= 45:
            raise ValueError("Oyuncu yaşı geçersiz")
        if min(
            self.current_value_score,
            self.injury_days_last_365,
            self.minutes_last_365,
            self.annual_salary,
            self.estimated_fee,
            self.contract_months_remaining,
            self.league_strength,
        ) < 0:
            raise ValueError("Transfer girdileri negatif olamaz")

@dataclass(frozen=True)
class TransferAssessment:
    player_id: str
    performance_score: float
    age_curve_score: float
    injury_risk_score: float
    cost_efficiency_score: float
    contract_leverage_score: float
    league_adjustment_score: float
    overall_score: float
    recommendation: str
    warnings: tuple[str, ...]
