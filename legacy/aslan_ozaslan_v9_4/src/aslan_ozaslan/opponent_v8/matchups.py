from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PlayerMatchup:
    our_player_id: str
    opponent_player_id: str
    zone: str
    our_score: float
    opponent_score: float
    pace_edge: float
    aerial_edge: float
    pressure_edge: float

    def validate(self) -> None:
        if not self.our_player_id.strip() or not self.opponent_player_id.strip():
            raise ValueError("Oyuncu kimlikleri boş olamaz")
        for value in (
            self.our_score,
            self.opponent_score,
            self.pace_edge,
            self.aerial_edge,
            self.pressure_edge,
        ):
            if not -1 <= value <= 1:
                raise ValueError("Eşleşme metriği -1 ile 1 arasında olmalıdır")

@dataclass(frozen=True)
class MatchupAssessment:
    label: str
    advantage_score: float
    explanation: str

class PlayerMatchupEngine:
    def evaluate(self, matchup: PlayerMatchup) -> MatchupAssessment:
        matchup.validate()

        base = matchup.our_score - matchup.opponent_score
        advantage = (
            base * 0.50
            + matchup.pace_edge * 0.22
            + matchup.aerial_edge * 0.10
            + matchup.pressure_edge * 0.18
        )
        advantage = max(-1.0, min(advantage, 1.0))

        if advantage >= 0.15:
            label = "OUR_ADVANTAGE"
        elif advantage <= -0.15:
            label = "OPPONENT_ADVANTAGE"
        else:
            label = "BALANCED"

        return MatchupAssessment(
            label=label,
            advantage_score=advantage,
            explanation=(
                f"{matchup.zone} bölgesinde hesaplanan eşleşme avantajı "
                f"{advantage:+.3f}."
            ),
        )
