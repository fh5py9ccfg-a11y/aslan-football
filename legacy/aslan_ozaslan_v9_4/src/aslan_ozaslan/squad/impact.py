from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PlayerAvailability:
    player_id: str
    expected_minutes_share: float
    attack_value: float
    defense_value: float
    status: str

@dataclass(frozen=True)
class SquadImpact:
    attack_multiplier: float
    defense_multiplier: float
    unavailable_count: int
    uncertainty_penalty: float

class SquadImpactCalculator:
    VALID_STATUSES = {"AVAILABLE", "DOUBTFUL", "OUT", "SUSPENDED", "UNKNOWN"}

    def calculate(self, players: list[PlayerAvailability]) -> SquadImpact:
        attack_loss = 0.0
        defense_loss = 0.0
        unavailable = 0
        uncertainty = 0.0

        for player in players:
            if player.status not in self.VALID_STATUSES:
                raise ValueError(f"Geçersiz oyuncu durumu: {player.status}")
            if not 0 <= player.expected_minutes_share <= 1:
                raise ValueError("expected_minutes_share 0 ile 1 arasında olmalıdır")

            weight = player.expected_minutes_share
            if player.status in {"OUT", "SUSPENDED"}:
                unavailable += 1
                attack_loss += max(player.attack_value, 0.0) * weight
                defense_loss += max(player.defense_value, 0.0) * weight
            elif player.status == "DOUBTFUL":
                uncertainty += 0.03 * weight
                attack_loss += max(player.attack_value, 0.0) * weight * 0.35
                defense_loss += max(player.defense_value, 0.0) * weight * 0.35
            elif player.status == "UNKNOWN":
                uncertainty += 0.06 * weight

        attack_multiplier = max(0.70, 1.0 - min(attack_loss, 0.30))
        defense_multiplier = min(1.30, 1.0 + min(defense_loss, 0.30))

        return SquadImpact(
            attack_multiplier=round(attack_multiplier, 4),
            defense_multiplier=round(defense_multiplier, 4),
            unavailable_count=unavailable,
            uncertainty_penalty=round(min(uncertainty, 0.30), 4),
        )
