from __future__ import annotations
from dataclasses import dataclass
from statistics import mean, pstdev

@dataclass(frozen=True)
class PositionMetricProfile:
    position: str
    metric_name: str
    mean_value: float
    standard_deviation: float

class PositionNormalizer:
    def normalize(self, value: float, profile: PositionMetricProfile) -> float:
        if profile.standard_deviation <= 0:
            raise ValueError("Standart sapma pozitif olmalıdır")
        return (value - profile.mean_value) / profile.standard_deviation

    def build_profile(
        self,
        *,
        position: str,
        metric_name: str,
        values: list[float],
    ) -> PositionMetricProfile:
        if len(values) < 2:
            raise ValueError("Profil için en az iki örnek gerekir")
        deviation = pstdev(values)
        if deviation == 0:
            deviation = 1.0
        return PositionMetricProfile(
            position=position,
            metric_name=metric_name,
            mean_value=mean(values),
            standard_deviation=deviation,
        )
