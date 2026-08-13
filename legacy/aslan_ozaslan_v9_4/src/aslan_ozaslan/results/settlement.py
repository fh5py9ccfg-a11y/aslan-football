from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class MatchResult:
    fixture_id: str
    home_goals: int
    away_goals: int

    @property
    def outcome(self) -> int:
        if self.home_goals > self.away_goals:
            return 0
        if self.home_goals == self.away_goals:
            return 1
        return 2

@dataclass(frozen=True)
class SettledPrediction:
    calculation_id: str
    fixture_id: str
    predicted_outcome: int
    actual_outcome: int
    correct: bool
    confidence: int
    model_version: str

class SettlementEngine:
    def settle(self, prediction, result: MatchResult) -> SettledPrediction:
        if prediction.fixture_id != result.fixture_id:
            raise ValueError("Tahmin ile maç sonucu aynı fixture için olmalıdır")
        if prediction.status != "OK":
            raise ValueError("BLOCKED veya eksik tahmin sonuçlandırılamaz")
        probabilities = (
            prediction.home_probability,
            prediction.draw_probability,
            prediction.away_probability,
        )
        if any(value is None for value in probabilities):
            raise ValueError("Olasılıklar eksik")
        predicted = max(range(3), key=lambda index: probabilities[index])
        actual = result.outcome
        return SettledPrediction(
            calculation_id=prediction.calculation_id,
            fixture_id=prediction.fixture_id,
            predicted_outcome=predicted,
            actual_outcome=actual,
            correct=predicted == actual,
            confidence=prediction.data_confidence,
            model_version=prediction.model_version,
        )
