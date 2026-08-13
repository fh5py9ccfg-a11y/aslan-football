from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class TacticalRecommendationContext:
    fixture_id: str
    minute: int
    goal_difference: int
    possession: float
    pressing: float
    defensive_line: float
    width: float
    tempo: float
    momentum_edge: float
    fatigue_level: float
    reliability_score: float

    def validate(self) -> None:
        if not self.fixture_id.strip():
            raise ValueError("fixture_id boş olamaz")
        if not 0 <= self.minute <= 130:
            raise ValueError("minute geçersiz")
        for value in (
            self.possession,
            self.pressing,
            self.defensive_line,
            self.width,
            self.tempo,
            self.fatigue_level,
            self.reliability_score,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Bağlam metrikleri 0 ile 1 arasında olmalıdır")

@dataclass(frozen=True)
class AgentOpinion:
    agent_name: str
    recommendation: str
    confidence: float
    risk: float
    rationale: str

@dataclass(frozen=True)
class TacticalRecommendation:
    action: str
    confidence: float
    risk: float
    urgency: str
    rationale: tuple[str, ...]
    approved: bool
