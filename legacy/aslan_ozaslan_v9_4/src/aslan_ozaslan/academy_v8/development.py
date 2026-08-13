from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class YouthDevelopmentProjection:
    level_6m: float
    level_12m: float
    level_24m: float
    growth_rate: float
    trajectory: str

class YouthDevelopmentModel:
    def project(
        self,
        *,
        age: int,
        current_level: float,
        potential_level: float,
        attendance: float,
        minutes_share: float,
        discipline_score: float,
    ) -> YouthDevelopmentProjection:
        if not 14 <= age <= 23:
            raise ValueError("age geçersiz")
        for value in (
            current_level,
            potential_level,
            attendance,
            minutes_share,
            discipline_score,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Gelişim girdileri geçersiz")

        headroom = max(0.0, potential_level - current_level)
        age_factor = (
            1.00 if age <= 17
            else 0.90 if age <= 19
            else 0.75 if age <= 21
            else 0.55
        )
        environment = (
            attendance * 0.40
            + minutes_share * 0.35
            + discipline_score * 0.25
        )
        growth_rate = headroom * age_factor * environment

        level_6m = min(1.0, current_level + growth_rate * 0.28)
        level_12m = min(1.0, current_level + growth_rate * 0.52)
        level_24m = min(1.0, current_level + growth_rate)

        if growth_rate >= 0.16:
            trajectory = "ELITE_GROWTH"
        elif growth_rate >= 0.09:
            trajectory = "STRONG_GROWTH"
        elif growth_rate >= 0.04:
            trajectory = "STEADY_GROWTH"
        else:
            trajectory = "STALLED"

        return YouthDevelopmentProjection(
            level_6m=level_6m,
            level_12m=level_12m,
            level_24m=level_24m,
            growth_rate=growth_rate,
            trajectory=trajectory,
        )
