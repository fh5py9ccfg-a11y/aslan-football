from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class DriftAlert:
    triggered: bool
    metric: str
    baseline: float
    recent: float
    degradation: float
    message: str

class DriftDetector:
    def __init__(self, accuracy_drop_threshold: float = 0.10):
        if not 0 < accuracy_drop_threshold < 1:
            raise ValueError("Eşik 0 ile 1 arasında olmalıdır")
        self.accuracy_drop_threshold = accuracy_drop_threshold

    def detect_accuracy_drift(self, baseline_accuracy: float, recent_accuracy: float) -> DriftAlert:
        for value in (baseline_accuracy, recent_accuracy):
            if not 0 <= value <= 1:
                raise ValueError("Doğruluk 0 ile 1 arasında olmalıdır")
        degradation = baseline_accuracy - recent_accuracy
        triggered = degradation >= self.accuracy_drop_threshold
        return DriftAlert(
            triggered=triggered,
            metric="accuracy",
            baseline=baseline_accuracy,
            recent=recent_accuracy,
            degradation=round(degradation, 4),
            message=(
                "Model performansında anlamlı düşüş tespit edildi."
                if triggered
                else "Anlamlı model bozulması tespit edilmedi."
            ),
        )
