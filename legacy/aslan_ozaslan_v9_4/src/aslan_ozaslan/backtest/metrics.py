from dataclasses import dataclass
from math import log

@dataclass(frozen=True)
class BacktestMetrics:
    matches: int
    accuracy: float
    brier_score: float
    log_loss: float

def evaluate_probabilities(probabilities, outcomes):
    if len(probabilities) != len(outcomes) or not probabilities:
        raise ValueError("Olasılık ve sonuç listeleri aynı ve boş olmayan uzunlukta olmalıdır")
    correct = 0
    brier_total = 0.0
    log_total = 0.0
    for probs, outcome in zip(probabilities, outcomes):
        if outcome not in (0, 1, 2):
            raise ValueError("Sonuç yalnızca 0, 1 veya 2 olabilir")
        if any(p < 0 or p > 1 for p in probs) or abs(sum(probs) - 1.0) > 1e-6:
            raise ValueError("Geçersiz olasılık dağılımı")
        correct += int(max(range(3), key=lambda i: probs[i]) == outcome)
        target = [0.0, 0.0, 0.0]
        target[outcome] = 1.0
        brier_total += sum((p-y)**2 for p, y in zip(probs, target)) / 3.0
        log_total += -log(max(probs[outcome], 1e-12))
    n = len(outcomes)
    return BacktestMetrics(n, round(correct/n,4), round(brier_total/n,6), round(log_total/n,6))
