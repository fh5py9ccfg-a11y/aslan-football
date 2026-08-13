from __future__ import annotations
from dataclasses import dataclass

from aslan_ozaslan.live_v5 import LiveMatchEvent

@dataclass(frozen=True)
class ProviderEventRecord:
    provider_event_id: str
    fixture_id: str
    minute: int
    team_id: str
    event_type: str
    value: float = 1.0
    corrected: bool = False
    cancelled: bool = False

    def validate(self) -> None:
        if not self.provider_event_id.strip():
            raise ValueError("provider_event_id boş olamaz")
        if not self.fixture_id.strip() or not self.team_id.strip():
            raise ValueError("fixture_id ve team_id boş olamaz")
        if not 0 <= self.minute <= 130:
            raise ValueError("minute geçersiz")
        if self.value < 0:
            raise ValueError("value negatif olamaz")

class ProviderEventMapper:
    TYPE_MAP = {
        "goal": "GOAL",
        "shot": "SHOT",
        "shot_on_target": "SHOT_ON_TARGET",
        "red_card": "RED_CARD",
        "yellow_card": "YELLOW_CARD",
        "dangerous_attack": "DANGEROUS_ATTACK",
        "substitution": "SUBSTITUTION",
    }

    def map(self, record: ProviderEventRecord) -> LiveMatchEvent | None:
        record.validate()
        if record.cancelled:
            return None

        mapped_type = self.TYPE_MAP.get(record.event_type.lower())
        if mapped_type is None:
            raise ValueError(
                f"Desteklenmeyen provider event türü: {record.event_type}"
            )

        suffix = ":corrected" if record.corrected else ""
        return LiveMatchEvent(
            event_id=f"{record.fixture_id}:{record.provider_event_id}{suffix}",
            minute=record.minute,
            team_id=record.team_id,
            event_type=mapped_type,
            value=record.value,
        )
