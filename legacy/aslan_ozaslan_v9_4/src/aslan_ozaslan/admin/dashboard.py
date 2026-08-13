from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdminDashboardSnapshot:
    provider_status: str
    champion_model: str | None
    pending_fixtures: int
    unsettled_predictions: int
    drift_alerts: int
    release_ready: bool


class AdminDashboard:
    def build(
        self,
        *,
        provider_status: str,
        champion_model: str | None,
        pending_fixtures: int,
        unsettled_predictions: int,
        drift_alerts: int,
        release_ready: bool,
    ) -> AdminDashboardSnapshot:
        for value in (pending_fixtures, unsettled_predictions, drift_alerts):
            if value < 0:
                raise ValueError("Sayaçlar negatif olamaz")
        return AdminDashboardSnapshot(
            provider_status=provider_status,
            champion_model=champion_model,
            pending_fixtures=pending_fixtures,
            unsettled_predictions=unsettled_predictions,
            drift_alerts=drift_alerts,
            release_ready=release_ready,
        )
