from dataclasses import dataclass

@dataclass(frozen=True)
class SquadPlayer:
    player_id: str
    position: str
    role: str
    value_score: float
    fatigue: float
    available: bool

    def validate(self):
        if not self.player_id.strip() or not self.position.strip() or not self.role.strip():
            raise ValueError("Kadro oyuncusu alanları boş olamaz")
        if self.value_score < 0:
            raise ValueError("value_score negatif olamaz")
        if not 0 <= self.fatigue <= 1:
            raise ValueError("fatigue 0 ile 1 arasında olmalıdır")

@dataclass(frozen=True)
class FormationRequirement:
    position: str
    count: int

    def validate(self):
        if not self.position.strip() or self.count <= 0:
            raise ValueError("Geçersiz formasyon gereksinimi")
