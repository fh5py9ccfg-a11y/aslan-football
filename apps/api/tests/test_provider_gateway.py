from apps.api.app.provider_gateway import (
    EventReconciler,
    GenericJsonProviderAdapter,
    ProviderGateway,
    ProviderQualityEngine,
    ProviderTrustRepository,
    RawProviderEvent,
)


class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value


def build_gateway():
    redis = Redis()
    repository = ProviderTrustRepository(
        redis,
        prefix="trust",
    )
    return ProviderGateway(
        adapters=(
            GenericJsonProviderAdapter("p1"),
            GenericJsonProviderAdapter("p2"),
        ),
        quality_engine=ProviderQualityEngine(
            repository=repository
        ),
        reconciler=EventReconciler(
            trust_repository=repository
        ),
    )


def raw(provider, event_id, team_id="t1", at=100):
    return RawProviderEvent(
        provider=provider,
        provider_event_id=event_id,
        match_id="m1",
        event_type="goal",
        occurred_at=at,
        payload={
            "team_id": team_id,
            "player_id": "player-1",
            "value": 1,
        },
        received_at=at + 1,
    )


def test_provider_event_is_normalized():
    gateway = build_gateway()

    event = gateway.ingest(raw("p1", "e1"))

    assert event.event_type == "GOAL"
    assert event.match_id == "m1"
    assert event.quality_score == 100
    assert len(event.raw_digest) == 64


def test_duplicate_reduces_provider_trust():
    gateway = build_gateway()

    gateway.ingest(raw("p1", "e1"))
    gateway.ingest(raw("p1", "e1"))

    trust = gateway.quality_engine.repository.get("p1")

    assert trust.total_events == 2
    assert trust.duplicate_events == 1
    assert trust.score < 100


def test_reconciliation_selects_higher_trust_provider():
    gateway = build_gateway()
    first = gateway.ingest(raw("p1", "e1"))
    second = gateway.ingest(raw("p2", "e2"))

    gateway.quality_engine.record(
        provider="p1",
        valid=False,
        event_time=100,
    )

    result = gateway.reconcile((first, second))

    assert result.selected.provider == "p2"
    assert result.conflict is False


def test_conflicting_events_are_reported():
    gateway = build_gateway()
    first = gateway.ingest(
        raw("p1", "e1", team_id="home")
    )
    second = gateway.ingest(
        raw("p2", "e2", team_id="away")
    )

    result = gateway.reconcile((first, second))

    assert result.conflict is True
