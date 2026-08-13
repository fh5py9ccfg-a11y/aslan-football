from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .slo_adapter import SLOMeasurement


@dataclass
class PrometheusSLOSource:
    query: Callable[[str], float]
    name: str = "prometheus"

    def measure(self, objective_name: str, window_days: int) -> SLOMeasurement:
        if objective_name == "availability":
            expression = (
                f"sum(rate(http_requests_total{{status!~'5..'}}[{window_days}d])) "
                f"/ sum(rate(http_requests_total[{window_days}d]))"
            )
        elif objective_name == "prediction_pipeline_success":
            expression = (
                f"sum(rate(prediction_jobs_total{{status='success'}}[{window_days}d])) "
                f"/ sum(rate(prediction_jobs_total[{window_days}d]))"
            )
        else:
            raise ValueError(f"Desteklenmeyen SLO objective: {objective_name}")

        achieved = float(self.query(expression))
        return SLOMeasurement(
            name=objective_name,
            achieved=achieved,
            window_days=window_days,
            source=self.name,
        )
