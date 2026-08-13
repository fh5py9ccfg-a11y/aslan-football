from __future__ import annotations
from dataclasses import dataclass

from .backtest import FootballBacktestReport

@dataclass(frozen=True)
class BaselineComparison:
    candidate_better: bool
    brier_improvement: float
    log_loss_improvement: float
    accuracy_improvement: float

class BaselineComparator:
    def compare(
        self,
        candidate: FootballBacktestReport,
        baseline: FootballBacktestReport,
    ) -> BaselineComparison:
        if candidate.samples != baseline.samples:
            raise ValueError("Candidate ve baseline aynı örnek setinde değerlendirilmelidir")

        return BaselineComparison(
            candidate_better=(
                candidate.brier_score < baseline.brier_score
                and candidate.log_loss < baseline.log_loss
            ),
            brier_improvement=baseline.brier_score - candidate.brier_score,
            log_loss_improvement=baseline.log_loss - candidate.log_loss,
            accuracy_improvement=candidate.accuracy - baseline.accuracy,
        )
