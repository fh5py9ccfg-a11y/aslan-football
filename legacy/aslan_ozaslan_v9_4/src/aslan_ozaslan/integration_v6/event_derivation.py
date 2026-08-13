from __future__ import annotations

from aslan_ozaslan.live_v5 import LiveMatchEvent
from .domain import ProviderFixtureSnapshot

class SnapshotEventDeriver:
    def derive(
        self,
        current: ProviderFixtureSnapshot,
        previous: ProviderFixtureSnapshot | None,
    ) -> tuple[LiveMatchEvent, ...]:
        if previous is None:
            return ()

        events = []
        home_delta = current.home_score - previous.home_score
        away_delta = current.away_score - previous.away_score

        for index in range(home_delta):
            events.append(
                LiveMatchEvent(
                    event_id=(
                        f"{current.fixture_id}:home-goal:"
                        f"{current.home_score - home_delta + index + 1}"
                    ),
                    minute=current.minute,
                    team_id=current.home_team_id,
                    event_type="GOAL",
                    value=1.0,
                )
            )

        for index in range(away_delta):
            events.append(
                LiveMatchEvent(
                    event_id=(
                        f"{current.fixture_id}:away-goal:"
                        f"{current.away_score - away_delta + index + 1}"
                    ),
                    minute=current.minute,
                    team_id=current.away_team_id,
                    event_type="GOAL",
                    value=1.0,
                )
            )

        return tuple(events)
