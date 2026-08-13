from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class CalibrationBin:
    lower: float
    upper: float
    mean_probability: float
    observed_rate: float
    samples: int

@dataclass(frozen=True)
class CalibrationReport:
    bins: tuple[CalibrationBin, ...]
    expected_calibration_error: float

class ProbabilityCalibrationAnalyzer:
    def analyze(
        self,
        probabilities: list[float],
        outcomes: list[int],
        *,
        bins: int = 10,
    ) -> CalibrationReport:
        if len(probabilities) != len(outcomes) or not probabilities:
            raise ValueError("Olasılık ve sonuç dizileri eşit ve boş olmayan uzunlukta olmalıdır")
        if bins <= 0:
            raise ValueError("bins pozitif olmalıdır")

        bucket_data = [[] for _ in range(bins)]
        for probability, outcome in zip(probabilities, outcomes):
            if probability < 0 or probability > 1:
                raise ValueError("Olasılık 0 ile 1 arasında olmalıdır")
            if outcome not in (0, 1):
                raise ValueError("Sonuç 0 veya 1 olmalıdır")
            index = min(int(probability * bins), bins - 1)
            bucket_data[index].append((probability, outcome))

        result_bins = []
        total = len(probabilities)
        ece = 0.0

        for index, items in enumerate(bucket_data):
            if not items:
                continue
            lower = index / bins
            upper = (index + 1) / bins
            mean_probability = sum(item[0] for item in items) / len(items)
            observed_rate = sum(item[1] for item in items) / len(items)
            ece += (len(items) / total) * abs(mean_probability - observed_rate)
            result_bins.append(
                CalibrationBin(
                    lower=lower,
                    upper=upper,
                    mean_probability=mean_probability,
                    observed_rate=observed_rate,
                    samples=len(items),
                )
            )

        return CalibrationReport(
            bins=tuple(result_bins),
            expected_calibration_error=ece,
        )
