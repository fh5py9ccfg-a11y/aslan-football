from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ModelProbability:
    model_name: str
    home: float
    draw: float
    away: float
    weight: float

@dataclass(frozen=True)
class EnsemblePrediction:
    home: float
    draw: float
    away: float
    contributors: tuple[str, ...]

class WeightedEnsemble:
    def combine(self, predictions: list[ModelProbability]) -> EnsemblePrediction:
        if not predictions:
            raise ValueError("Ensemble için en az bir model gerekir")

        total_weight = 0.0
        home = draw = away = 0.0
        contributors = []

        for item in predictions:
            if item.weight <= 0:
                raise ValueError("Model ağırlığı pozitif olmalıdır")
            probabilities = (item.home, item.draw, item.away)
            if any(value < 0 or value > 1 for value in probabilities):
                raise ValueError("Olasılıklar 0 ile 1 arasında olmalıdır")
            if abs(sum(probabilities) - 1.0) > 1e-6:
                raise ValueError("Her model olasılık toplamı 1 olmalıdır")

            total_weight += item.weight
            home += item.home * item.weight
            draw += item.draw * item.weight
            away += item.away * item.weight
            contributors.append(item.model_name)

        return EnsemblePrediction(
            home=home / total_weight,
            draw=draw / total_weight,
            away=away / total_weight,
            contributors=tuple(contributors),
        )
