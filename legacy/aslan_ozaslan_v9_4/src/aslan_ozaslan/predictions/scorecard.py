from dataclasses import dataclass

@dataclass(frozen=True)
class Scorecard:
    settled_predictions: int
    accuracy: float
    average_confidence: float
    high_confidence_accuracy: float | None

class ScorecardCalculator:
    def calculate(self, rows):
        if not rows:
            return Scorecard(0, 0.0, 0.0, None)
        correct = 0
        confidence_total = 0
        high_total = 0
        high_correct = 0
        for probabilities, actual, confidence in rows:
            if actual not in (0,1,2):
                raise ValueError("actual 0, 1 veya 2 olmalıdır")
            if abs(sum(probabilities) - 1.0) > 1e-6:
                raise ValueError("Olasılıkların toplamı 1 olmalıdır")
            predicted = max(range(3), key=lambda i: probabilities[i])
            hit = predicted == actual
            correct += int(hit)
            confidence_total += confidence
            if confidence >= 75:
                high_total += 1
                high_correct += int(hit)
        n = len(rows)
        return Scorecard(
            n,
            round(correct/n,4),
            round(confidence_total/n,2),
            round(high_correct/high_total,4) if high_total else None,
        )
