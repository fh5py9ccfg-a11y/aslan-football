from __future__ import annotations

class AcademyValuationModel:
    def project_24m(
        self,
        *,
        current_market_value: float,
        projected_level_24m: float,
        age: int,
        first_team_readiness: float,
        injury_risk: float,
    ) -> float:
        if current_market_value < 0:
            raise ValueError("current_market_value negatif olamaz")
        for value in (
            projected_level_24m,
            first_team_readiness,
            injury_risk,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Değerleme girdileri geçersiz")
        if not 14 <= age <= 23:
            raise ValueError("age geçersiz")

        youth_multiplier = (
            1.55 if age <= 18
            else 1.35 if age <= 20
            else 1.18
        )
        quality_multiplier = 0.65 + projected_level_24m * 1.35
        readiness_multiplier = 0.80 + first_team_readiness * 0.50
        risk_multiplier = 1.0 - injury_risk * 0.35

        return (
            max(current_market_value, 100_000.0)
            * youth_multiplier
            * quality_multiplier
            * readiness_multiplier
            * risk_multiplier
        )
