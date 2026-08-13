from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ClubPlayerContract:
    player_id: str
    position: str
    age: int
    quality_score: float
    annual_salary: float
    market_value: float
    contract_months_remaining: int
    academy_eligible: bool = False

    def validate(self) -> None:
        if not self.player_id.strip() or not self.position.strip():
            raise ValueError("Oyuncu alanları boş olamaz")
        if not 15 <= self.age <= 45:
            raise ValueError("age geçersiz")
        for value in (
            self.quality_score,
            self.annual_salary,
            self.market_value,
            self.contract_months_remaining,
        ):
            if value < 0:
                raise ValueError("Kulüp girdileri negatif olamaz")

@dataclass(frozen=True)
class SquadPlanningReport:
    squad_size: int
    average_age: float
    total_salary: float
    total_market_value: float
    depth_score: float
    age_balance_score: float
    contract_risk_score: float
    recommendations: tuple[str, ...]

@dataclass(frozen=True)
class TransferScenarioResult:
    total_salary_before: float
    total_salary_after: float
    total_value_before: float
    total_value_after: float
    average_quality_before: float
    average_quality_after: float
    budget_delta: float
