from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DecisionContext:
    fixture_id: str
    minute: int
    home_probability: float
    draw_probability: float
    away_probability: float
    home_goals: int
    away_goals: int
    home_red_cards: int
    away_red_cards: int
    momentum_edge: float
    reliability_score: float

    def validate(self) -> None:
        if not self.fixture_id.strip():
            raise ValueError("fixture_id boş olamaz")
        if not 0 <= self.minute <= 130:
            raise ValueError("minute geçersiz")
        probabilities = (
            self.home_probability,
            self.draw_probability,
            self.away_probability,
        )
        if any(value < 0 or value > 1 for value in probabilities):
            raise ValueError("Olasılıklar 0 ile 1 arasında olmalıdır")
        if abs(sum(probabilities) - 1.0) > 1e-6:
            raise ValueError("Olasılık toplamı 1 olmalıdır")
        if min(
            self.home_goals,
            self.away_goals,
            self.home_red_cards,
            self.away_red_cards,
        ) < 0:
            raise ValueError("Skor ve kart değerleri negatif olamaz")
        if not 0 <= self.reliability_score <= 1:
            raise ValueError("reliability_score geçersiz")

@dataclass(frozen=True)
class DecisionSignal:
    signal_type: str
    side: str
    strength: float
    urgency: str
    explanation: str

@dataclass(frozen=True)
class DecisionSnapshot:
    fixture_id: str
    minute: int
    recommended_outcome: str
    confidence: float
    risk_score: float
    opportunity_score: float
    signals: tuple[DecisionSignal, ...]
