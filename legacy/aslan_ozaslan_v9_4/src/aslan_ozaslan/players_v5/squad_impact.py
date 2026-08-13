from __future__ import annotations
from dataclasses import dataclass

from .rating import PlayerValueScore

@dataclass(frozen=True)
class SquadAvailability:
    player_id: str
    available: bool
    expected_minutes_share: float

@dataclass(frozen=True)
class SquadImpactReport:
    total_available_value: float
    total_missing_value: float
    availability_ratio: float
    missing_player_ids: tuple[str, ...]

class SquadImpactAnalyzer:
    def analyze(
        self,
        scores: list[PlayerValueScore],
        availability: list[SquadAvailability],
    ) -> SquadImpactReport:
        score_map = {score.player_id: score for score in scores}
        available_value = 0.0
        missing_value = 0.0
        missing = []

        for item in availability:
            if item.player_id not in score_map:
                raise ValueError("Availability kaydı için oyuncu skoru bulunamadı")
            if not 0 <= item.expected_minutes_share <= 1:
                raise ValueError("expected_minutes_share 0 ile 1 arasında olmalıdır")

            weighted_value = (
                score_map[item.player_id].overall
                * item.expected_minutes_share
            )
            if item.available:
                available_value += weighted_value
            else:
                missing_value += weighted_value
                missing.append(item.player_id)

        total = available_value + missing_value
        return SquadImpactReport(
            total_available_value=available_value,
            total_missing_value=missing_value,
            availability_ratio=available_value / total if total else 1.0,
            missing_player_ids=tuple(sorted(missing)),
        )
