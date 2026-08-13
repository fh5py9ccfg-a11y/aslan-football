from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DuplicateAlert:
    triggered: bool
    signature: tuple[float, float, float] | None
    fixture_ids: tuple[str, ...]
    reason: str

class DuplicateProbabilityGuard:
    def __init__(self, threshold: int = 3, precision: int = 4):
        if threshold < 2:
            raise ValueError("threshold en az 2 olmalıdır")
        self.threshold = threshold
        self.precision = precision

    def inspect(self, rows: list[tuple[str, float, float, float]]) -> DuplicateAlert:
        groups: dict[tuple[float, float, float], list[str]] = {}
        for fixture_id, home, draw, away in rows:
            signature = (
                round(home, self.precision),
                round(draw, self.precision),
                round(away, self.precision),
            )
            groups.setdefault(signature, []).append(fixture_id)

        for signature, fixture_ids in groups.items():
            if len(fixture_ids) >= self.threshold:
                return DuplicateAlert(
                    triggered=True,
                    signature=signature,
                    fixture_ids=tuple(fixture_ids),
                    reason="Farklı maçlarda aynı olasılık dağılımı tekrarlandı.",
                )

        return DuplicateAlert(
            triggered=False,
            signature=None,
            fixture_ids=(),
            reason="Şüpheli tekrar bulunmadı.",
        )
