from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class Player:
    player_id: str
    team_id: str
    name: str
    position: str
    age: int

    def validate(self) -> None:
        if not all(value.strip() for value in (
            self.player_id, self.team_id, self.name, self.position
        )):
            raise ValueError("Oyuncu kimlik alanları boş olamaz")
        if not 15 <= self.age <= 50:
            raise ValueError("Oyuncu yaşı geçersiz")

@dataclass(frozen=True)
class PlayerMatchPerformance:
    player_id: str
    match_id: str
    minutes: int
    goals: int
    assists: int
    expected_goals: float
    expected_assists: float
    progressive_passes: int
    key_passes: int
    successful_dribbles: int
    pressures: int
    recoveries: int
    interceptions: int
    tackles_won: int
    duels_won: int
    duels_total: int

    def validate(self) -> None:
        integer_values = (
            self.minutes, self.goals, self.assists, self.progressive_passes,
            self.key_passes, self.successful_dribbles, self.pressures,
            self.recoveries, self.interceptions, self.tackles_won,
            self.duels_won, self.duels_total,
        )
        if any(value < 0 for value in integer_values):
            raise ValueError("Performans metrikleri negatif olamaz")
        if self.minutes > 130:
            raise ValueError("Dakika değeri geçersiz")
        if self.expected_goals < 0 or self.expected_assists < 0:
            raise ValueError("Expected metrikleri negatif olamaz")
        if self.duels_won > self.duels_total:
            raise ValueError("Kazanılan ikili mücadele toplamı aşamaz")
