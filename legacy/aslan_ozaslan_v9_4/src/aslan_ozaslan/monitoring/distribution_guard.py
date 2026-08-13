from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DistributionIncident:
    distribution: tuple[float, float, float]
    fixture_ids: tuple[str, ...]
    reason: str


class DistributionGuard:
    def __init__(self, repeat_threshold: int = 3, precision: int = 4):
        if repeat_threshold < 2:
            raise ValueError("repeat_threshold en az 2 olmalıdır")
        self.repeat_threshold = repeat_threshold
        self.precision = precision
        self._seen: dict[tuple[float, float, float], set[str]] = {}

    def observe(
        self,
        fixture_id: str,
        home_probability: float,
        draw_probability: float,
        away_probability: float,
    ) -> DistributionIncident | None:
        if not fixture_id.strip():
            raise ValueError("fixture_id zorunludur")
        distribution = tuple(
            round(value, self.precision)
            for value in (home_probability, draw_probability, away_probability)
        )
        fixtures = self._seen.setdefault(distribution, set())
        fixtures.add(fixture_id)
        if len(fixtures) >= self.repeat_threshold:
            return DistributionIncident(
                distribution=distribution,
                fixture_ids=tuple(sorted(fixtures)),
                reason="Farklı maçlarda aynı olasılık dağılımı tekrarlandı; tahmin akışı durdurulmalıdır.",
            )
        return None
