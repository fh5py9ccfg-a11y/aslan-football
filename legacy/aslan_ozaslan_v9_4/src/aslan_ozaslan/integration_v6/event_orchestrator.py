from __future__ import annotations
from dataclasses import dataclass

from .provider_events import ProviderEventRecord, ProviderEventMapper
from .event_repository import ProviderEventRepository
from .late_event import LateEventPolicy
from .reconciliation import SnapshotEventReconciler
from .domain import ProviderFixtureSnapshot

@dataclass(frozen=True)
class ProviderEventUpdate:
    accepted: bool
    changed: bool
    requires_replay: bool
    reconciliation_consistent: bool
    issues: tuple[str, ...]

class ProviderEventOrchestrator:
    def __init__(
        self,
        *,
        repository: ProviderEventRepository,
        live_processor,
        late_event_policy: LateEventPolicy | None = None,
    ):
        self.repository = repository
        self.live_processor = live_processor
        self.mapper = ProviderEventMapper()
        self.late_policy = late_event_policy or LateEventPolicy()
        self.reconciler = SnapshotEventReconciler()

    def process(
        self,
        *,
        snapshot: ProviderFixtureSnapshot,
        record: ProviderEventRecord,
    ) -> ProviderEventUpdate:
        decision = self.late_policy.evaluate(
            record,
            current_minute=snapshot.minute,
        )
        changed = self.repository.upsert(record)

        mapped = self.mapper.map(record)
        if mapped is not None and changed:
            self.live_processor.process(mapped)

        reconciliation = self.reconciler.reconcile(
            snapshot,
            self.repository.for_fixture(snapshot.fixture_id),
        )

        return ProviderEventUpdate(
            accepted=decision.accepted,
            changed=changed,
            requires_replay=decision.requires_replay or record.corrected,
            reconciliation_consistent=reconciliation.consistent,
            issues=reconciliation.issues,
        )
