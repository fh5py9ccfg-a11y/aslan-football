from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class ModelMetrics:
    samples: int
    brier_score: float
    log_loss: float
    accuracy: float
    calibration_error: float


@dataclass(frozen=True)
class ModelComparison:
    champion_id: str
    challenger_id: str
    winner: str
    champion_metrics: ModelMetrics
    challenger_metrics: ModelMetrics
    reason: str


class ModelEvaluator:
    @staticmethod
    def evaluate(
        probabilities: tuple[float, ...],
        outcomes: tuple[int, ...],
    ) -> ModelMetrics:
        if len(probabilities) != len(outcomes):
            raise ValueError(
                "Probability ve outcome uzunlukları eşit olmalıdır"
            )
        if not probabilities:
            raise ValueError(
                "En az bir örnek gereklidir"
            )

        eps = 1e-12
        brier = 0.0
        log_loss = 0.0
        correct = 0
        calibration = 0.0

        for probability, outcome in zip(
            probabilities,
            outcomes,
        ):
            if not 0 <= probability <= 1:
                raise ValueError(
                    "Probability 0 ile 1 arasında olmalıdır"
                )
            if outcome not in {0, 1}:
                raise ValueError(
                    "Outcome 0 veya 1 olmalıdır"
                )

            brier += (probability - outcome) ** 2
            clipped = min(
                1 - eps,
                max(eps, probability),
            )
            log_loss += -(
                outcome * math.log(clipped)
                + (1 - outcome)
                * math.log(1 - clipped)
            )
            predicted = 1 if probability >= 0.5 else 0
            correct += int(predicted == outcome)
            calibration += abs(probability - outcome)

        count = len(probabilities)
        return ModelMetrics(
            samples=count,
            brier_score=round(brier / count, 6),
            log_loss=round(log_loss / count, 6),
            accuracy=round(correct / count, 6),
            calibration_error=round(
                calibration / count,
                6,
            ),
        )

    @staticmethod
    def compare(
        *,
        champion_id: str,
        challenger_id: str,
        champion_metrics: ModelMetrics,
        challenger_metrics: ModelMetrics,
        minimum_accuracy_gain: float = 0.0,
    ) -> ModelComparison:
        challenger_better = (
            challenger_metrics.brier_score
            < champion_metrics.brier_score
            and challenger_metrics.log_loss
            < champion_metrics.log_loss
            and challenger_metrics.accuracy
            >= champion_metrics.accuracy
            + minimum_accuracy_gain
        )

        winner = (
            challenger_id
            if challenger_better
            else champion_id
        )
        return ModelComparison(
            champion_id=champion_id,
            challenger_id=challenger_id,
            winner=winner,
            champion_metrics=champion_metrics,
            challenger_metrics=challenger_metrics,
            reason=(
                "Challenger tüm kalite kapılarını geçti"
                if challenger_better
                else "Champion kalite kapılarını korudu"
            ),
        )


class ProbabilityCalibrator:
    def __init__(
        self,
        *,
        slope: float = 1.0,
        intercept: float = 0.0,
    ):
        self.slope = slope
        self.intercept = intercept

    def calibrate(self, probability: float) -> float:
        if not 0 <= probability <= 1:
            raise ValueError(
                "Probability 0 ile 1 arasında olmalıdır"
            )

        eps = 1e-12
        clipped = min(
            1 - eps,
            max(eps, probability),
        )
        logit = math.log(
            clipped / (1 - clipped)
        )
        calibrated_logit = (
            self.slope * logit
            + self.intercept
        )
        calibrated = 1 / (
            1 + math.exp(-calibrated_logit)
        )
        return round(calibrated, 6)
