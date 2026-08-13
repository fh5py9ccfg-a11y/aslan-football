from __future__ import annotations
from datetime import datetime, timezone

from aslan_ozaslan.providers_v6 import NormalizedLiveFixture
from .domain import ProviderFixtureSnapshot

class SportmonksAnalyticsBridge:
    def to_snapshot(
        self,
        fixture: NormalizedLiveFixture,
    ) -> ProviderFixtureSnapshot:
        missing = []
        for name, value in (
            ("provider_fixture_id", fixture.provider_fixture_id),
            ("minute", fixture.minute),
            ("home_team_id", fixture.home_team_id),
            ("away_team_id", fixture.away_team_id),
            ("home_score", fixture.home_score),
            ("away_score", fixture.away_score),
            ("state", fixture.state),
        ):
            if value is None:
                missing.append(name)

        if missing:
            raise ValueError(
                "Canlı fixture alanları eksik: " + ", ".join(missing)
            )

        return ProviderFixtureSnapshot(
            fixture_id=str(fixture.provider_fixture_id),
            minute=int(fixture.minute),
            home_team_id=str(fixture.home_team_id),
            away_team_id=str(fixture.away_team_id),
            home_score=int(fixture.home_score),
            away_score=int(fixture.away_score),
            state=str(fixture.state),
            updated_at=datetime.now(timezone.utc).isoformat(),
        )
