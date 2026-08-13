from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelValidationScore:
    model_name: str
    brier_score: float
    log_loss: float

@dataclass(frozen=True)
class ModelWeight:
    model_name: str
    weight: float

class ValidationWeightCalculator:
    def calculate(self, scores: list[ModelValidationScore]) -> tuple[ModelWeight, ...]:
        if not scores:
            raise ValueError("Model skoru gereklidir")
        raw = []
        for score in scores:
            if score.brier_score <= 0 or score.log_loss <= 0:
                raise ValueError("Metrikler pozitif olmalıdır")
            quality = 1.0 / (score.brier_score + score.log_loss)
            raw.append((score.model_name, quality))

        total = sum(value for _, value in raw)
        return tuple(
            ModelWeight(model_name=name, weight=value / total)
            for name, value in raw
        )
