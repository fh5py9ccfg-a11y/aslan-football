from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class WindowMetrics:
    count: int
    accuracy: float
    log_loss: float
    brier_score: float


@dataclass(frozen=True)
class WindowedDriftReport:
    triggered: bool
    accuracy_drop: float
    log_loss_increase: float
    brier_increase: float
    reasons: tuple[str, ...]


class WindowedDriftDetector:
    def __init__(
        self,
        *,
        accuracy_drop_threshold: float = 0.10,
        log_loss_increase_threshold: float = 0.12,
        brier_increase_threshold: float = 0.05,
        minimum_window_size: int = 20,
    ):
        self.accuracy_drop_threshold = accuracy_drop_threshold
        self.log_loss_increase_threshold = log_loss_increase_threshold
        self.brier_increase_threshold = brier_increase_threshold
        self.minimum_window_size = minimum_window_size

    def metrics(self, rows) -> WindowMetrics:
        rows = list(rows)
        if len(rows) < self.minimum_window_size:
            raise ValueError("Drift ölçümü için örnek sayısı yetersiz")
        correct = 0
        log_loss_total = 0.0
        brier_total = 0.0

        for probabilities, actual in rows:
            if actual not in (0, 1, 2):
                raise ValueError("Gerçek sonuç 0, 1 veya 2 olmalıdır")
            if abs(sum(probabilities) - 1.0) > 1e-6:
                raise ValueError("Olasılıkların toplamı 1 olmalıdır")
            predicted = max(range(3), key=lambda index: probabilities[index])
            correct += int(predicted == actual)
            probability_of_actual = max(probabilities[actual], 1e-12)
            log_loss_total += -math.log(probability_of_actual)
            target = [0.0, 0.0, 0.0]
            target[actual] = 1.0
            brier_total += sum(
                (probabilities[index] - target[index]) ** 2
                for index in range(3)
            )

        count = len(rows)
        return WindowMetrics(
            count=count,
            accuracy=round(correct / count, 6),
            log_loss=round(log_loss_total / count, 6),
            brier_score=round(brier_total / count, 6),
        )

    def compare(self, baseline: WindowMetrics, recent: WindowMetrics) -> WindowedDriftReport:
        reasons = []
        accuracy_drop = baseline.accuracy - recent.accuracy
        log_loss_increase = recent.log_loss - baseline.log_loss
        brier_increase = recent.brier_score - baseline.brier_score

        if accuracy_drop >= self.accuracy_drop_threshold:
            reasons.append("accuracy_drop")
        if log_loss_increase >= self.log_loss_increase_threshold:
            reasons.append("log_loss_increase")
        if brier_increase >= self.brier_increase_threshold:
            reasons.append("brier_increase")

        return WindowedDriftReport(
            triggered=bool(reasons),
            accuracy_drop=round(accuracy_drop, 6),
            log_loss_increase=round(log_loss_increase, 6),
            brier_increase=round(brier_increase, 6),
            reasons=tuple(reasons),
        )
