from __future__ import annotations
from dataclasses import dataclass

from .rating import PlayerValueScore

@dataclass(frozen=True)
class PlayerFormTrend:
    player_id: str
    recent_average: float
    previous_average: float
    slope: float
    trend: str

class PlayerFormAnalyzer:
    def analyze(
        self,
        player_id: str,
        scores: list[PlayerValueScore],
        *,
        recent_window: int = 3,
    ) -> PlayerFormTrend:
        if recent_window <= 0:
            raise ValueError("recent_window pozitif olmalıdır")
        if len(scores) < 2:
            raise ValueError("Form analizi için en az iki skor gerekir")
        if any(score.player_id != player_id for score in scores):
            raise ValueError("Skorlar aynı oyuncuya ait olmalıdır")

        values = [score.overall for score in scores]
        recent = values[-recent_window:]
        previous = values[:-recent_window] or values[:1]
        recent_average = sum(recent) / len(recent)
        previous_average = sum(previous) / len(previous)
        slope = recent_average - previous_average

        if slope > 0.75:
            trend = "RISING"
        elif slope < -0.75:
            trend = "FALLING"
        else:
            trend = "STABLE"

        return PlayerFormTrend(
            player_id=player_id,
            recent_average=recent_average,
            previous_average=previous_average,
            slope=slope,
            trend=trend,
        )
