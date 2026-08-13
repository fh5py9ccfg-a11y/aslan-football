from __future__ import annotations
from dataclasses import dataclass
from statistics import mean, pstdev

@dataclass(frozen=True)
class ModelVote:
    model_name: str
    home_probability: float
    draw_probability: float
    away_probability: float

@dataclass(frozen=True)
class ConsensusReport:
    consensus_score: float
    dispersion: float
    dominant_outcome: str
    confidence_label: str

class EnsembleConsensusAnalyzer:
    def analyze(self, votes: list[ModelVote]) -> ConsensusReport:
        if not votes:
            raise ValueError("En az bir model oyu gereklidir")

        for vote in votes:
            probabilities = (
                vote.home_probability,
                vote.draw_probability,
                vote.away_probability,
            )
            if any(value < 0 or value > 1 for value in probabilities):
                raise ValueError("Olasılıklar 0 ile 1 arasında olmalıdır")
            if abs(sum(probabilities) - 1.0) > 1e-6:
                raise ValueError("Model olasılık toplamı 1 olmalıdır")

        home_values = [vote.home_probability for vote in votes]
        draw_values = [vote.draw_probability for vote in votes]
        away_values = [vote.away_probability for vote in votes]

        means = {
            "HOME": mean(home_values),
            "DRAW": mean(draw_values),
            "AWAY": mean(away_values),
        }
        dominant = max(means, key=means.get)

        dispersions = [
            pstdev(values) if len(values) > 1 else 0.0
            for values in (home_values, draw_values, away_values)
        ]
        dispersion = sum(dispersions) / 3.0
        consensus = max(0.0, min(1.0, 1.0 - dispersion * 3.0))

        if consensus >= 0.85:
            label = "HIGH"
        elif consensus >= 0.65:
            label = "MEDIUM"
        else:
            label = "LOW"

        return ConsensusReport(
            consensus_score=consensus,
            dispersion=dispersion,
            dominant_outcome=dominant,
            confidence_label=label,
        )
