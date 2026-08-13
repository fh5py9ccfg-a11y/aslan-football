from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExplanationFactor:
    name: str
    direction: str
    strength: float
    evidence: str

@dataclass(frozen=True)
class PredictionExplanation:
    headline: str
    factors: tuple[ExplanationFactor, ...]
    limitations: tuple[str, ...]

class ExplanationBuilder:
    VALID_DIRECTIONS = {"HOME", "DRAW", "AWAY", "NEUTRAL"}

    def build(
        self,
        *,
        probabilities: tuple[float, float, float],
        factors: list[ExplanationFactor],
        limitations: list[str],
    ) -> PredictionExplanation:
        if abs(sum(probabilities) - 1.0) > 1e-6:
            raise ValueError("Olasılıkların toplamı 1 olmalıdır")
        for factor in factors:
            if factor.direction not in self.VALID_DIRECTIONS:
                raise ValueError(f"Geçersiz yön: {factor.direction}")
            if not 0 <= factor.strength <= 1:
                raise ValueError("Faktör gücü 0 ile 1 arasında olmalıdır")

        labels = ("Ev sahibi", "Beraberlik", "Deplasman")
        index = max(range(3), key=lambda i: probabilities[i])
        headline = f"En yüksek olasılık: {labels[index]} %{probabilities[index] * 100:.1f}"

        ordered = tuple(sorted(factors, key=lambda item: (-item.strength, item.name)))
        return PredictionExplanation(
            headline=headline,
            factors=ordered,
            limitations=tuple(limitations),
        )
