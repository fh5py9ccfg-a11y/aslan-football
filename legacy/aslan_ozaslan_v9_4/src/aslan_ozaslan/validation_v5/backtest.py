from __future__ import annotations
from dataclasses import dataclass
from math import log

@dataclass(frozen=True)
class MatchPredictionSample:
    home_probability: float
    draw_probability: float
    away_probability: float
    outcome: str

@dataclass(frozen=True)
class FootballBacktestReport:
    samples: int
    accuracy: float
    brier_score: float
    log_loss: float

class FootballBacktester:
    OUTCOMES = ("HOME", "DRAW", "AWAY")

    def evaluate(self, samples: list[MatchPredictionSample]) -> FootballBacktestReport:
        if not samples:
            raise ValueError("Backtest için örnek gereklidir")

        correct = 0
        brier_total = 0.0
        log_total = 0.0

        for sample in samples:
            probabilities = {
                "HOME": sample.home_probability,
                "DRAW": sample.draw_probability,
                "AWAY": sample.away_probability,
            }
            if sample.outcome not in self.OUTCOMES:
                raise ValueError("Geçersiz maç sonucu")
            if any(value < 0 or value > 1 for value in probabilities.values()):
                raise ValueError("Olasılıklar 0 ile 1 arasında olmalıdır")
            if abs(sum(probabilities.values()) - 1.0) > 1e-6:
                raise ValueError("Olasılıkların toplamı 1 olmalıdır")

            predicted = max(probabilities, key=probabilities.get)
            correct += int(predicted == sample.outcome)

            for outcome, probability in probabilities.items():
                target = 1.0 if outcome == sample.outcome else 0.0
                brier_total += (probability - target) ** 2

            observed_probability = max(probabilities[sample.outcome], 1e-15)
            log_total += -log(observed_probability)

        count = len(samples)
        return FootballBacktestReport(
            samples=count,
            accuracy=correct / count,
            brier_score=brier_total / count,
            log_loss=log_total / count,
        )
