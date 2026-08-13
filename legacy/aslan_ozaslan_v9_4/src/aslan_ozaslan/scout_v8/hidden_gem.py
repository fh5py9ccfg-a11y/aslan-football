from __future__ import annotations

class HiddenGemDetector:
    def score(
        self,
        *,
        current_level: float,
        potential_level: float,
        market_value: float,
        annual_salary: float,
        age: int,
        risk_score: float,
    ) -> float:
        for value in (current_level, potential_level, risk_score):
            if not 0 <= value <= 1:
                raise ValueError("Hidden gem girdileri geçersiz")
        if market_value < 0 or annual_salary < 0:
            raise ValueError("Maliyet girdileri negatif olamaz")

        upside = max(0.0, potential_level - current_level)
        age_bonus = max(0.0, min((27 - age) / 12.0, 1.0))
        affordability = 1.0 / (
            1.0
            + market_value / 10_000_000.0
            + annual_salary / 2_000_000.0
        )
        score = (
            upside * 0.40
            + age_bonus * 0.20
            + affordability * 0.25
            + (1.0 - risk_score) * 0.15
        )
        return max(0.0, min(score, 1.0))
