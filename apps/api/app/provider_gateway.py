from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time
from typing import Protocol


@dataclass(frozen=True)
class RawProviderEvent:
    provider: str
    provider_event_id: str
    match_id: str
    event_type: str
    occurred_at: int
    payload: dict
    received_at: int


@dataclass(frozen=True)
class NormalizedMatchEvent:
    event_id: str
    match_id: str
    event_type: str
    occurred_at: int
    team_id: str | None
    player_id: str | None
    value: float | None
    provider: str
    provider_event_id: str
    quality_score: int
    raw_digest: str


@dataclass(frozen=True)
class ProviderTrustState:
    provider: str
    score: int
    total_events: int
    valid_events: int
    duplicate_events: int
    conflicting_events: int
    last_event_at: int | None
    updated_at: int


@dataclass(frozen=True)
class ReconciliationResult:
    selected: NormalizedMatchEvent
    alternatives: tuple[NormalizedMatchEvent, ...]
    conflict: bool
    reason: str


class ProviderAdapter(Protocol):
    name: str

    def normalize(
        self,
        raw: RawProviderEvent,
    ) -> NormalizedMatchEvent:
        ...


class GenericJsonProviderAdapter:
    def __init__(self, name: str):
        self.name = name

    def normalize(
        self,
        raw: RawProviderEvent,
    ) -> NormalizedMatchEvent:
        if raw.provider != self.name:
            raise ValueError(
                "Provider adapter ile event provider uyuşmuyor"
            )

        event_type = raw.event_type.strip().upper()
        if event_type not in {
            "GOAL",
            "SHOT",
            "SHOT_ON_TARGET",
            "YELLOW_CARD",
            "RED_CARD",
            "SUBSTITUTION",
            "PENALTY",
            "VAR",
            "CORNER",
            "POSSESSION",
        }:
            raise ValueError(
                f"Desteklenmeyen event type: {event_type}"
            )

        canonical = json.dumps(
            raw.payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()

        team_id = raw.payload.get("team_id")
        player_id = raw.payload.get("player_id")
        value = raw.payload.get("value")
        if value is not None:
            value = float(value)

        completeness = 100
        if not raw.match_id:
            completeness -= 40
        if not raw.provider_event_id:
            completeness -= 25
        if event_type in {"GOAL", "SHOT", "SHOT_ON_TARGET"}:
            if not team_id:
                completeness -= 20
        if raw.occurred_at <= 0:
            completeness -= 30

        event_id = hashlib.sha256(
            (
                f"{raw.provider}|{raw.provider_event_id}|"
                f"{raw.match_id}|{event_type}|{raw.occurred_at}"
            ).encode("utf-8")
        ).hexdigest()

        return NormalizedMatchEvent(
            event_id=event_id,
            match_id=raw.match_id,
            event_type=event_type,
            occurred_at=raw.occurred_at,
            team_id=(
                str(team_id)
                if team_id is not None
                else None
            ),
            player_id=(
                str(player_id)
                if player_id is not None
                else None
            ),
            value=value,
            provider=raw.provider,
            provider_event_id=raw.provider_event_id,
            quality_score=max(0, min(100, completeness)),
            raw_digest=digest,
        )


class ProviderTrustRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:provider-trust",
        ttl_seconds: int = 2_592_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def get(
        self,
        provider: str,
    ) -> ProviderTrustState:
        payload = self.client.get(self._key(provider))
        if payload is None:
            return ProviderTrustState(
                provider=provider,
                score=100,
                total_events=0,
                valid_events=0,
                duplicate_events=0,
                conflicting_events=0,
                last_event_at=None,
                updated_at=0,
            )
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ProviderTrustState(**json.loads(payload))

    def save(
        self,
        state: ProviderTrustState,
    ) -> ProviderTrustState:
        self.client.setex(
            self._key(state.provider),
            self.ttl_seconds,
            json.dumps(
                state.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        return state

    def _key(self, provider: str) -> str:
        return f"{self.prefix}:{provider}"


class ProviderQualityEngine:
    def __init__(
        self,
        *,
        repository,
    ):
        self.repository = repository

    def record(
        self,
        *,
        provider: str,
        valid: bool,
        duplicate: bool = False,
        conflict: bool = False,
        event_time: int | None = None,
        now: int | None = None,
    ) -> ProviderTrustState:
        current = int(now if now is not None else time.time())
        state = self.repository.get(provider)

        total = state.total_events + 1
        valid_events = state.valid_events + (1 if valid else 0)
        duplicate_events = (
            state.duplicate_events
            + (1 if duplicate else 0)
        )
        conflicting_events = (
            state.conflicting_events
            + (1 if conflict else 0)
        )

        valid_ratio = valid_events / total
        duplicate_ratio = duplicate_events / total
        conflict_ratio = conflicting_events / total

        score = round(
            100
            * valid_ratio
            - 25
            * duplicate_ratio
            - 40
            * conflict_ratio
        )

        updated = ProviderTrustState(
            provider=provider,
            score=max(0, min(100, score)),
            total_events=total,
            valid_events=valid_events,
            duplicate_events=duplicate_events,
            conflicting_events=conflicting_events,
            last_event_at=event_time,
            updated_at=current,
        )
        return self.repository.save(updated)


class EventReconciler:
    def __init__(
        self,
        *,
        trust_repository,
        timestamp_tolerance_seconds: int = 5,
    ):
        self.trust_repository = trust_repository
        self.timestamp_tolerance_seconds = (
            timestamp_tolerance_seconds
        )

    def reconcile(
        self,
        events: tuple[NormalizedMatchEvent, ...],
    ) -> ReconciliationResult:
        if not events:
            raise ValueError(
                "Reconciliation için en az bir event gerekir"
            )

        ordered = sorted(
            events,
            key=lambda item: (
                self.trust_repository.get(
                    item.provider
                ).score,
                item.quality_score,
                -abs(
                    item.occurred_at
                    - min(
                        event.occurred_at
                        for event in events
                    )
                ),
            ),
            reverse=True,
        )
        selected = ordered[0]

        conflicts = []
        for event in ordered[1:]:
            same_identity = (
                event.match_id == selected.match_id
                and event.event_type == selected.event_type
            )
            timestamp_close = (
                abs(
                    event.occurred_at
                    - selected.occurred_at
                )
                <= self.timestamp_tolerance_seconds
            )
            same_team = event.team_id == selected.team_id
            if not (
                same_identity
                and timestamp_close
                and same_team
            ):
                conflicts.append(event)

        return ReconciliationResult(
            selected=selected,
            alternatives=tuple(ordered[1:]),
            conflict=bool(conflicts),
            reason=(
                "En yüksek provider güveni ve event kalite puanı seçildi"
                if not conflicts
                else "Provider event'leri arasında çelişki bulundu"
            ),
        )


class ProviderGateway:
    def __init__(
        self,
        *,
        adapters: tuple[ProviderAdapter, ...],
        quality_engine,
        reconciler,
    ):
        self.adapters = {
            adapter.name: adapter
            for adapter in adapters
        }
        self.quality_engine = quality_engine
        self.reconciler = reconciler
        self._seen = set()

    def ingest(
        self,
        raw: RawProviderEvent,
    ) -> NormalizedMatchEvent:
        adapter = self.adapters.get(raw.provider)
        if adapter is None:
            self.quality_engine.record(
                provider=raw.provider,
                valid=False,
                event_time=raw.occurred_at,
            )
            raise KeyError(
                f"Provider adapter bulunamadı: {raw.provider}"
            )

        duplicate_key = (
            raw.provider,
            raw.provider_event_id,
        )
        duplicate = duplicate_key in self._seen

        try:
            normalized = adapter.normalize(raw)
        except Exception:
            self.quality_engine.record(
                provider=raw.provider,
                valid=False,
                duplicate=duplicate,
                event_time=raw.occurred_at,
            )
            raise

        self._seen.add(duplicate_key)
        self.quality_engine.record(
            provider=raw.provider,
            valid=True,
            duplicate=duplicate,
            event_time=raw.occurred_at,
        )
        return normalized

    def reconcile(
        self,
        events: tuple[NormalizedMatchEvent, ...],
    ) -> ReconciliationResult:
        result = self.reconciler.reconcile(events)
        if result.conflict:
            for event in events:
                self.quality_engine.record(
                    provider=event.provider,
                    valid=True,
                    conflict=True,
                    event_time=event.occurred_at,
                )
        return result
