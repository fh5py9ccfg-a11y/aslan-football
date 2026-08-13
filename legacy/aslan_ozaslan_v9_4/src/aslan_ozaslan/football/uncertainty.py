from __future__ import annotations
from dataclasses import dataclass
from math import log

@dataclass(frozen=True)
class PredictionUncertainty:
    entropy: float
    normalized_entropy: float
    confidence_label: str

class PredictionUncertaintyAnalyzer:
    def evaluate(self, home: float, draw: float, away: float) -> PredictionUncertainty:
        probabilities = (home, draw, away)
        if any(value < 0 or value > 1 for value in probabilities):
            raise ValueError("Olasılıklar 0 ile 1 arasında olmalıdır")
        if abs(sum(probabilities) - 1.0) > 1e-6:
            raise ValueError("Olasılık toplamı 1 olmalıdır")

        entropy = -sum(value * log(value) for value in probabilities if value > 0)
        maximum = log(3)
        normalized = entropy / maximum if maximum else 0.0

        if normalized < 0.45:
            label = "HIGH"
        elif normalized < 0.75:
            label = "MEDIUM"
        else:
            label = "LOW"

        return PredictionUncertainty(
            entropy=entropy,
            normalized_entropy=normalized,
            confidence_label=label,
        )
