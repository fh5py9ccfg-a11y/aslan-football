from __future__ import annotations
from dataclasses import dataclass

from .domain import PlayerMatchPerformance

@dataclass(frozen=True)
class PlayerValueScore:
    player_id: str
    attacking: float
    creativity: float
    progression: float
    defensive: float
    pressing: float
    reliability: float
    overall: float

class PlayerValueCalculator:
    def calculate(
        self,
        performance: PlayerMatchPerformance,
        *,
        expected_minutes: int = 90,
    ) -> PlayerValueScore:
        performance.validate()
        if expected_minutes <= 0:
            raise ValueError("expected_minutes pozitif olmalıdır")

        minute_factor = min(performance.minutes / expected_minutes, 1.0)

        attacking = (
            performance.goals * 7.0
            + performance.expected_goals * 4.0
            + performance.successful_dribbles * 0.5
        )
        creativity = (
            performance.assists * 6.0
            + performance.expected_assists * 4.0
            + performance.key_passes * 0.8
        )
        progression = (
            performance.progressive_passes * 0.25
            + performance.successful_dribbles * 0.4
        )
        defensive = (
            performance.recoveries * 0.25
            + performance.interceptions * 0.8
            + performance.tackles_won * 0.7
        )
        pressing = performance.pressures * 0.08

        duel_ratio = (
            performance.duels_won / performance.duels_total
            if performance.duels_total else 0.0
        )
        reliability = minute_factor * 6.0 + duel_ratio * 4.0

        weighted = (
            attacking * 0.28
            + creativity * 0.22
            + progression * 0.15
            + defensive * 0.20
            + pressing * 0.08
            + reliability * 0.07
        )

        return PlayerValueScore(
            player_id=performance.player_id,
            attacking=attacking,
            creativity=creativity,
            progression=progression,
            defensive=defensive,
            pressing=pressing,
            reliability=reliability,
            overall=weighted,
        )
