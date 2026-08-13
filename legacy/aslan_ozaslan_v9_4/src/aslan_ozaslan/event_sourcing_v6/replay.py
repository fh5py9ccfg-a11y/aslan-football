from dataclasses import dataclass
import time
from .domain import AggregateSnapshot
from .projector import MatchStateProjector

@dataclass(frozen=True)
class ReplayReport:
    state: object
    replayed_events: int
    used_snapshot: bool
    duration_ms: float

class MatchReplayEngine:
    def __init__(self, event_store, snapshot_repository, projector=None, snapshot_interval=100):
        if snapshot_interval <= 0:
            raise ValueError("snapshot_interval pozitif olmalıdır")
        self.event_store = event_store
        self.snapshots = snapshot_repository
        self.projector = projector or MatchStateProjector()
        self.snapshot_interval = snapshot_interval

    def replay(self, fixture_id, home_team_id, away_team_id, up_to_sequence=None):
        started = time.perf_counter()
        snapshot = self.snapshots.load(fixture_id)
        use_snapshot = snapshot is not None and (
            up_to_sequence is None or snapshot.last_sequence <= up_to_sequence
        )
        if use_snapshot:
            state = snapshot.state
            after = snapshot.last_sequence
        else:
            state = self.projector.initial(fixture_id, home_team_id, away_team_id)
            after = -1
        events = self.event_store.stream(fixture_id, after, up_to_sequence)
        replayed = 0
        for event in events:
            state = self.projector.apply(state, event)
            replayed += 1
            if state.processed_events % self.snapshot_interval == 0:
                self.snapshots.save(AggregateSnapshot(fixture_id, state.last_sequence, state))
        return ReplayReport(
            state, replayed, use_snapshot,
            (time.perf_counter() - started) * 1000.0
        )
