from __future__ import annotations

from .domain import PlayerDNA

class ClubFitEvaluator:
    def evaluate(
        self,
        *,
        player: PlayerDNA,
        desired: PlayerDNA,
    ) -> float:
        player.validate()
        desired.validate()

        weights = (
            0.12, 0.12, 0.10, 0.12, 0.12,
            0.08, 0.10, 0.10, 0.08, 0.06,
        )
        player_values = (
            player.passing,
            player.progression,
            player.dribbling,
            player.pressing,
            player.defending,
            player.aerial,
            player.finishing,
            player.creativity,
            player.athleticism,
            player.consistency,
        )
        desired_values = (
            desired.passing,
            desired.progression,
            desired.dribbling,
            desired.pressing,
            desired.defending,
            desired.aerial,
            desired.finishing,
            desired.creativity,
            desired.athleticism,
            desired.consistency,
        )

        distance = sum(
            abs(a - b) * weight
            for a, b, weight in zip(
                player_values,
                desired_values,
                weights,
            )
        )
        return max(0.0, min(1.0 - distance, 1.0))
