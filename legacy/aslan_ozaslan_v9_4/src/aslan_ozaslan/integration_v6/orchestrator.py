from __future__ import annotations

from aslan_ozaslan.live_v5 import LiveProbabilityState, LiveMatchProcessor
from .domain import ProviderFixtureSnapshot, AnalyticsUpdate
from .fixture_state import FixtureStateGuard
from .event_derivation import SnapshotEventDeriver
from .repository import FixtureSnapshotRepository

class ProviderToAnalyticsOrchestrator:
    def __init__(
        self,
        *,
        repository: FixtureSnapshotRepository,
        initial_home_probability: float = 0.45,
        initial_draw_probability: float = 0.30,
        initial_away_probability: float = 0.25,
    ):
        self.repository = repository
        self.initial_probabilities = (
            initial_home_probability,
            initial_draw_probability,
            initial_away_probability,
        )
        self.guard = FixtureStateGuard()
        self.deriver = SnapshotEventDeriver()
        self._processors = {}

    def process(
        self,
        snapshot: ProviderFixtureSnapshot,
    ) -> AnalyticsUpdate:
        previous = self.repository.load(snapshot.fixture_id)
        decision = self.guard.evaluate(snapshot, previous)
        if not decision.accepted:
            return AnalyticsUpdate(
                fixture_id=snapshot.fixture_id,
                accepted=False,
                reason=decision.reason,
                home_probability=None,
                draw_probability=None,
                away_probability=None,
                event_count=0,
            )

        processor = self._processors.get(snapshot.fixture_id)
        if processor is None:
            home_p, draw_p, away_p = self.initial_probabilities
            processor = LiveMatchProcessor(
                home_team_id=snapshot.home_team_id,
                away_team_id=snapshot.away_team_id,
                initial_state=LiveProbabilityState(
                    minute=previous.minute if previous else 0,
                    home_probability=home_p,
                    draw_probability=draw_p,
                    away_probability=away_p,
                    home_goals=previous.home_score if previous else 0,
                    away_goals=previous.away_score if previous else 0,
                    home_red_cards=0,
                    away_red_cards=0,
                ),
            )
            self._processors[snapshot.fixture_id] = processor

        events = self.deriver.derive(snapshot, previous)

        for event in events:
            processor.process(event)

        if not events and snapshot.minute > processor.state.minute:
            processor.state = LiveProbabilityState(
                minute=snapshot.minute,
                home_probability=processor.state.home_probability,
                draw_probability=processor.state.draw_probability,
                away_probability=processor.state.away_probability,
                home_goals=snapshot.home_score,
                away_goals=snapshot.away_score,
                home_red_cards=processor.state.home_red_cards,
                away_red_cards=processor.state.away_red_cards,
            )

        self.repository.save(snapshot)
        state = processor.state

        return AnalyticsUpdate(
            fixture_id=snapshot.fixture_id,
            accepted=True,
            reason="updated",
            home_probability=state.home_probability,
            draw_probability=state.draw_probability,
            away_probability=state.away_probability,
            event_count=len(events),
        )
