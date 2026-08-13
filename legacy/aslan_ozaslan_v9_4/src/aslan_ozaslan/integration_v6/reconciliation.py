from __future__ import annotations
from dataclasses import dataclass

from .domain import ProviderFixtureSnapshot
from .provider_events import ProviderEventRecord

@dataclass(frozen=True)
class ReconciliationReport:
    consistent: bool
    home_goal_events: int
    away_goal_events: int
    snapshot_home_score: int
    snapshot_away_score: int
    issues: tuple[str, ...]

class SnapshotEventReconciler:
    def reconcile(
        self,
        snapshot: ProviderFixtureSnapshot,
        events: tuple[ProviderEventRecord, ...],
    ) -> ReconciliationReport:
        home_goals = sum(
            1 for event in events
            if (
                not event.cancelled
                and event.event_type.lower() == "goal"
                and event.team_id == snapshot.home_team_id
            )
        )
        away_goals = sum(
            1 for event in events
            if (
                not event.cancelled
                and event.event_type.lower() == "goal"
                and event.team_id == snapshot.away_team_id
            )
        )

        issues = []
        if home_goals != snapshot.home_score:
            issues.append("home_goal_mismatch")
        if away_goals != snapshot.away_score:
            issues.append("away_goal_mismatch")

        return ReconciliationReport(
            consistent=not issues,
            home_goal_events=home_goals,
            away_goal_events=away_goals,
            snapshot_home_score=snapshot.home_score,
            snapshot_away_score=snapshot.away_score,
            issues=tuple(issues),
        )
