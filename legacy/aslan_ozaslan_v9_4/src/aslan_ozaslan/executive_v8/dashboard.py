from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExecutiveDashboardSnapshot:
    club_id: str
    health_score: float
    objective_progress: float
    financial_stability: float
    strategic_risk: float
    status: str
    action_count: int

class ExecutiveDashboardService:
    def build(self, report) -> ExecutiveDashboardSnapshot:
        return ExecutiveDashboardSnapshot(
            club_id=report.club_id,
            health_score=report.health_score,
            objective_progress=report.objective_progress,
            financial_stability=report.financial_stability,
            strategic_risk=report.strategic_risk,
            status=report.status,
            action_count=len(report.priority_actions),
        )
