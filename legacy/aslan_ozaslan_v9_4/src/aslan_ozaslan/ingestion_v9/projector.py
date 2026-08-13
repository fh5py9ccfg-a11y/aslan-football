from __future__ import annotations
from datetime import datetime, timezone

from aslan_ozaslan.event_sourcing_v6 import DomainEvent

class ProviderEventProjector:
    def __init__(self, event_store):
        self.event_store = event_store

    def project(self, normalized_event) -> bool:
        sequence = self.event_store.last_sequence(
            normalized_event.fixture_id
        ) + 1

        event = DomainEvent(
            event_id=(
                f"provider:{normalized_event.fixture_id}:"
                f"{normalized_event.event_id}"
            ),
            fixture_id=normalized_event.fixture_id,
            sequence=sequence,
            event_type=normalized_event.event_type,
            occurred_at=datetime.now(timezone.utc).isoformat(),
            payload={
                "minute": normalized_event.minute,
                "extra_minute": normalized_event.extra_minute,
                "team_id": normalized_event.team_id,
                "player_id": normalized_event.player_id,
                "cancelled": normalized_event.cancelled,
            },
            correlation_id=normalized_event.fixture_id,
            causation_id=normalized_event.event_id,
            metadata={"source": "sportmonks"},
        )
        return self.event_store.append(event)
