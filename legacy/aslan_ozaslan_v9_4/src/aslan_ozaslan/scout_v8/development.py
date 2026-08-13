from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DevelopmentProjection:
    level_6m: float
    level_12m: float
    level_24m: float
    trajectory: str

class PlayerDevelopmentProjector:
    def project(
        self,
        *,
        age: int,
        current_level: float,
        potential_level: float,
        consistency: float,
        minutes_share: float,
    ) -> DevelopmentProjection:
        if not 15 <= age <= 45:
            raise ValueError("age geçersiz")
        for value in (
            current_level,
            potential_level,
            consistency,
            minutes_share,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Gelişim girdileri geçersiz")

        headroom = max(0.0, potential_level - current_level)
        age_factor = (
            1.0 if age <= 21
            else 0.82 if age <= 24
            else 0.58 if age <= 27
            else 0.30 if age <= 30
            else 0.10
        )
        development_rate = (
            headroom
            * age_factor
            * (0.45 + consistency * 0.30 + minutes_share * 0.25)
        )

        level_6m = min(1.0, current_level + development_rate * 0.30)
        level_12m = min(1.0, current_level + development_rate * 0.55)
        level_24m = min(1.0, current_level + development_rate)

        gain = level_24m - current_level
        if gain >= 0.15:
            trajectory = "HIGH_GROWTH"
        elif gain >= 0.07:
            trajectory = "STEADY_GROWTH"
        else:
            trajectory = "LIMITED_GROWTH"

        return DevelopmentProjection(
            level_6m=level_6m,
            level_12m=level_12m,
            level_24m=level_24m,
            trajectory=trajectory,
        )
