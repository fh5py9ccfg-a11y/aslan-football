from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ClubExecutiveSnapshot:
    club_id: str
    sporting_score: float
    financial_score: float
    squad_score: float
    academy_score: float
    transfer_score: float
    risk_score: float
    revenue: float
    wage_cost: float
    transfer_balance: float
    average_squad_age: float

    def validate(self) -> None:
        if not self.club_id.strip():
            raise ValueError("club_id boş olamaz")
        for value in (
            self.sporting_score,
            self.financial_score,
            self.squad_score,
            self.academy_score,
            self.transfer_score,
            self.risk_score,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Yönetim skorları 0 ile 1 arasında olmalıdır")
        if min(self.revenue, self.wage_cost) < 0:
            raise ValueError("Finansal değerler negatif olamaz")
        if not 15 <= self.average_squad_age <= 40:
            raise ValueError("average_squad_age geçersiz")

@dataclass(frozen=True)
class SeasonObjective:
    name: str
    target_value: float
    current_value: float
    weight: float
    higher_is_better: bool = True

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Hedef adı boş olamaz")
        if self.weight <= 0:
            raise ValueError("weight pozitif olmalıdır")

@dataclass(frozen=True)
class ExecutiveDecisionReport:
    club_id: str
    health_score: float
    objective_progress: float
    financial_stability: float
    strategic_risk: float
    priority_actions: tuple[str, ...]
    status: str
