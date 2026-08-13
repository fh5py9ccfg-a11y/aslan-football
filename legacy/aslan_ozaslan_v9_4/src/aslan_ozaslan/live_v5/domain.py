from dataclasses import dataclass

@dataclass(frozen=True)
class LiveMatchEvent:
    event_id: str
    minute: int
    team_id: str
    event_type: str
    value: float = 1.0
    def validate(self):
        if not self.event_id.strip() or not self.team_id.strip(): raise ValueError('Event kimlik alanları boş olamaz')
        if not 0 <= self.minute <= 130: raise ValueError('Event dakikası geçersiz')
        if self.event_type not in {'GOAL','SHOT','SHOT_ON_TARGET','RED_CARD','YELLOW_CARD','DANGEROUS_ATTACK','SUBSTITUTION'}:
            raise ValueError('Desteklenmeyen event türü')
        if self.value < 0: raise ValueError('Event değeri negatif olamaz')

@dataclass(frozen=True)
class LiveProbabilityState:
    minute: int
    home_probability: float
    draw_probability: float
    away_probability: float
    home_goals: int
    away_goals: int
    home_red_cards: int
    away_red_cards: int
