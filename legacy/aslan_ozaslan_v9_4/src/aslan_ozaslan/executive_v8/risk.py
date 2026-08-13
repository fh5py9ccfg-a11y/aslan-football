from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class StrategicRiskReport:
    score: float
    level: str
    factors: tuple[str, ...]

class StrategicRiskEvaluator:
    def evaluate(
        self,
        *,
        squad_age: float,
        contract_risk: float,
        wage_ratio: float,
        academy_score: float,
        sporting_volatility: float,
    ) -> StrategicRiskReport:
        if not 15 <= squad_age <= 40:
            raise ValueError("squad_age geçersiz")
        for value in (
            contract_risk,
            wage_ratio,
            academy_score,
            sporting_volatility,
        ):
            if value < 0:
                raise ValueError("Risk girdileri negatif olamaz")

        age_risk = max(0.0, min((squad_age - 26.5) / 6.0, 1.0))
        wage_risk = max(0.0, min((wage_ratio - 0.55) / 0.40, 1.0))
        score = min(
            age_risk * 0.22
            + min(contract_risk, 1.0) * 0.24
            + wage_risk * 0.24
            + (1.0 - min(academy_score, 1.0)) * 0.14
            + min(sporting_volatility, 1.0) * 0.16,
            1.0,
        )

        factors = []
        if age_risk >= 0.45:
            factors.append("squad_ageing")
        if contract_risk >= 0.30:
            factors.append("contract_exposure")
        if wage_risk >= 0.45:
            factors.append("wage_pressure")
        if academy_score < 0.55:
            factors.append("academy_pipeline_weak")
        if sporting_volatility >= 0.45:
            factors.append("sporting_volatility")

        if score >= 0.70:
            level = "CRITICAL"
        elif score >= 0.45:
            level = "ELEVATED"
        else:
            level = "CONTROLLED"

        return StrategicRiskReport(
            score=score,
            level=level,
            factors=tuple(factors or ("no_major_factor",)),
        )
