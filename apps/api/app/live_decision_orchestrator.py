from __future__ import annotations

from dataclasses import dataclass
import asyncio
import hashlib
import json
import time

from .inference_platform import InferenceRequest


@dataclass(frozen=True)
class LiveDecisionRecord:
    decision_id: str
    match_id: str
    trigger: str
    slot: str
    model_id: str
    prediction: float
    confidence: float
    fallback_used: bool
    explanation: dict | None
    feature_snapshot: dict
    status: str
    created_at: int


class DecisionCooldownActive(RuntimeError):
    pass


class DuplicateDecision(RuntimeError):
    pass


class RedisLiveDecisionRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:live-decision",
        ttl_seconds: int = 604800,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def reserve(
        self,
        *,
        match_id: str,
        trigger: str,
        event_time: int,
    ) -> str:
        decision_id = hashlib.sha256(
            f"{match_id}|{trigger}|{event_time}".encode("utf-8")
        ).hexdigest()
        reserved = self.client.set(
            self._reservation_key(decision_id),
            "1",
            nx=True,
            ex=self.ttl_seconds,
        )
        if not reserved:
            raise DuplicateDecision(
                "Canlı karar daha önce işlendi"
            )
        return decision_id

    def check_cooldown(
        self,
        *,
        match_id: str,
        trigger: str,
        now: int,
        cooldown_seconds: int,
    ) -> None:
        payload = self.client.get(
            self._cooldown_key(match_id, trigger)
        )
        if payload is None:
            return
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        last_at = int(payload)
        if now - last_at < cooldown_seconds:
            raise DecisionCooldownActive(
                "Canlı karar cooldown süresi devam ediyor"
            )

    def mark_cooldown(
        self,
        *,
        match_id: str,
        trigger: str,
        now: int,
        cooldown_seconds: int,
    ) -> None:
        self.client.setex(
            self._cooldown_key(match_id, trigger),
            cooldown_seconds,
            str(now),
        )

    def save(
        self,
        record: LiveDecisionRecord,
    ) -> LiveDecisionRecord:
        self.client.setex(
            self._record_key(record.decision_id),
            self.ttl_seconds,
            json.dumps(
                record.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._record_index(record.match_id),
            record.decision_id,
        )
        return record

    def list_records(
        self,
        match_id: str,
        *,
        limit: int = 100,
    ) -> tuple[LiveDecisionRecord, ...]:
        items = []
        for decision_id in self.client.smembers(
            self._record_index(match_id)
        ):
            if isinstance(decision_id, bytes):
                decision_id = decision_id.decode("utf-8")
            payload = self.client.get(
                self._record_key(str(decision_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                LiveDecisionRecord(**json.loads(payload))
            )
        items.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def _reservation_key(self, decision_id: str) -> str:
        return f"{self.prefix}:reservation:{decision_id}"

    def _cooldown_key(
        self,
        match_id: str,
        trigger: str,
    ) -> str:
        return f"{self.prefix}:cooldown:{match_id}:{trigger}"

    def _record_key(self, decision_id: str) -> str:
        return f"{self.prefix}:record:{decision_id}"

    def _record_index(self, match_id: str) -> str:
        return f"{self.prefix}:records:{match_id}"


class LiveDecisionOrchestrator:
    def __init__(
        self,
        *,
        repository,
        inference_service,
        cooldown_seconds: int = 30,
        max_attempts: int = 2,
    ):
        self.repository = repository
        self.inference_service = inference_service
        self.cooldown_seconds = cooldown_seconds
        self.max_attempts = max_attempts

    async def execute(
        self,
        *,
        match_id: str,
        trigger: str,
        event_time: int,
        slot: str,
        tenant_id: str,
        feature_snapshot: dict,
        explain: bool = True,
        now: int | None = None,
    ) -> LiveDecisionRecord:
        current = int(
            now if now is not None
            else time.time()
        )

        self.repository.check_cooldown(
            match_id=match_id,
            trigger=trigger,
            now=current,
            cooldown_seconds=self.cooldown_seconds,
        )

        decision_id = self.repository.reserve(
            match_id=match_id,
            trigger=trigger,
            event_time=event_time,
        )

        request = InferenceRequest(
            request_id=decision_id,
            tenant_id=tenant_id,
            slot=slot,
            entity_id=match_id,
            features=feature_snapshot,
            explain=explain,
            latency_class="REALTIME",
        )

        last_error = None
        result = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                result = await self.inference_service.infer(
                    request
                )
                break
            except Exception as exc:
                last_error = exc
                if attempt < self.max_attempts:
                    await asyncio.sleep(0)

        if result is None:
            raise RuntimeError(
                f"Live decision inference başarısız: {last_error}"
            )

        record = LiveDecisionRecord(
            decision_id=decision_id,
            match_id=match_id,
            trigger=trigger,
            slot=slot,
            model_id=result.model_id,
            prediction=result.prediction,
            confidence=result.confidence,
            fallback_used=result.fallback_used,
            explanation=result.explanation,
            feature_snapshot=feature_snapshot,
            status="COMPLETED",
            created_at=current,
        )
        self.repository.save(record)
        self.repository.mark_cooldown(
            match_id=match_id,
            trigger=trigger,
            now=current,
            cooldown_seconds=self.cooldown_seconds,
        )
        return record

    @staticmethod
    def snapshot_from_streaming(
        snapshot,
    ) -> dict:
        return {
            "home_xg": snapshot.home_xg,
            "away_xg": snapshot.away_xg,
            "home_momentum": snapshot.home_momentum,
            "away_momentum": snapshot.away_momentum,
            "possession_trend": snapshot.possession_trend,
            "anomaly_score": snapshot.anomaly_score,
            "event_count": snapshot.event_count,
        }
