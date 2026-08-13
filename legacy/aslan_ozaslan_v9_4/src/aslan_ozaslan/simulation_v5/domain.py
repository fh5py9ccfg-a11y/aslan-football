from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MatchState:
    minute: int
    home_goals: int
    away_goals: int
    home_red_cards: int
    away_red_cards: int

    def validate(self) -> None:
        if not 0 <= self.minute <= 130:
            raise ValueError("Dakika geçersiz")
        if min(
            self.home_goals,
            self.away_goals,
            self.home_red_cards,
            self.away_red_cards,
        ) < 0:
            raise ValueError("Maç durumu negatif değer içeremez")

@dataclass(frozen=True)
class MatchSimulationInput:
    home_team_id: str
    away_team_id: str
    home_expected_goals: float
    away_expected_goals: float
    home_red_card_probability: float
    away_red_card_probability: float

    def validate(self) -> None:
        if not self.home_team_id.strip() or not self.away_team_id.strip():
            raise ValueError("Takım kimliği boş olamaz")
        if self.home_team_id == self.away_team_id:
            raise ValueError("Takım kendisiyle oynayamaz")
        if self.home_expected_goals < 0 or self.away_expected_goals < 0:
            raise ValueError("Expected goals negatif olamaz")
        if not 0 <= self.home_red_card_probability <= 1:
            raise ValueError("Ev kırmızı kart olasılığı geçersiz")
        if not 0 <= self.away_red_card_probability <= 1:
            raise ValueError("Deplasman kırmızı kart olasılığı geçersiz")
