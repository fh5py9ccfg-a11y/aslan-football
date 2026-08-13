from dataclasses import dataclass

@dataclass(frozen=True)
class FatigueInput:
    minutes_last_14_days: int
    matches_last_14_days: int
    rest_days: float
    travel_hours: float

@dataclass(frozen=True)
class FatigueAssessment:
    fatigue_score: float
    risk_level: str
    availability_multiplier: float

class FatigueModel:
    def assess(self, item):
        if min(item.minutes_last_14_days, item.matches_last_14_days,
               item.rest_days, item.travel_hours) < 0:
            raise ValueError("Yorgunluk girdileri negatif olamaz")
        fatigue = min(
            min(item.minutes_last_14_days / 1260, 1) * .45 +
            min(item.matches_last_14_days / 6, 1) * .25 +
            max(0, (4 - item.rest_days) / 4) * .20 +
            min(item.travel_hours / 12, 1) * .10,
            1,
        )
        risk = "HIGH" if fatigue >= .75 else "MEDIUM" if fatigue >= .45 else "LOW"
        return FatigueAssessment(fatigue, risk, max(.35, 1 - fatigue * .55))
