from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class OpponentDNA:
    team_id: str
    possession: float
    directness: float
    pressing: float
    defensive_line: float
    transition_speed: float
    left_attack_share: float
    right_attack_share: float
    central_attack_share: float
    set_piece_threat: float
    build_up_risk: float

    def validate(self) -> None:
        if not self.team_id.strip():
            raise ValueError("team_id boş olamaz")
        values = (
            self.possession,
            self.directness,
            self.pressing,
            self.defensive_line,
            self.transition_speed,
            self.left_attack_share,
            self.right_attack_share,
            self.central_attack_share,
            self.set_piece_threat,
            self.build_up_risk,
        )
        if any(value < 0 or value > 1 for value in values):
            raise ValueError("Rakip DNA metrikleri 0 ile 1 arasında olmalıdır")

@dataclass(frozen=True)
class WeaknessMap:
    left_defense: float
    right_defense: float
    central_defense: float
    transition_defense: float
    set_piece_defense: float
    pressure_resistance: float

@dataclass(frozen=True)
class MatchPlan:
    name: str
    pressing_level: float
    width: float
    tempo: float
    defensive_line: float
    primary_zone: str
    rationale: tuple[str, ...]

@dataclass(frozen=True)
class OpponentPreparationReport:
    opponent_id: str
    weakness_map: WeaknessMap
    critical_matchups: tuple[str, ...]
    plans: tuple[MatchPlan, ...]
    recommended_plan: str
    briefing: str
