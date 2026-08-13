import asyncio
import pytest

from apps.api.app.inference_platform import InferenceResult
from apps.api.app.live_decision_orchestrator import (
    DecisionCooldownActive,
    DuplicateDecision,
    LiveDecisionOrchestrator,
    RedisLiveDecisionRepository,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


class Inference:
    async def infer(self, request):
        return InferenceResult(
            request_id=request.request_id,
            model_id="m1",
            prediction=0.72,
            confidence=0.78,
            cached=False,
            fallback_used=False,
            latency_ms=2.0,
            explanation={"top_features": []},
        )


def build(cooldown=30):
    return LiveDecisionOrchestrator(
        repository=RedisLiveDecisionRepository(
            Redis(),
            prefix="decision",
        ),
        inference_service=Inference(),
        cooldown_seconds=cooldown,
        max_attempts=2,
    )


def test_live_decision_is_recorded():
    orchestrator = build()

    record = asyncio.run(
        orchestrator.execute(
            match_id="m1",
            trigger="MOMENTUM_SHIFT",
            event_time=100,
            slot="winner",
            tenant_id="tenant-a",
            feature_snapshot={"home_xg": 1.2},
            now=101,
        )
    )

    assert record.status == "COMPLETED"
    assert record.model_id == "m1"
    assert record.prediction == 0.72
    assert len(
        orchestrator.repository.list_records("m1")
    ) == 1


def test_duplicate_decision_is_rejected():
    orchestrator = build(cooldown=0)

    kwargs = dict(
        match_id="m1",
        trigger="MOMENTUM_SHIFT",
        event_time=100,
        slot="winner",
        tenant_id="tenant-a",
        feature_snapshot={"home_xg": 1.2},
        now=101,
    )
    asyncio.run(orchestrator.execute(**kwargs))

    with pytest.raises(DuplicateDecision):
        asyncio.run(orchestrator.execute(**kwargs))


def test_cooldown_blocks_new_trigger():
    orchestrator = build(cooldown=30)

    asyncio.run(
        orchestrator.execute(
            match_id="m1",
            trigger="MOMENTUM_SHIFT",
            event_time=100,
            slot="winner",
            tenant_id="tenant-a",
            feature_snapshot={"home_xg": 1.2},
            now=101,
        )
    )

    with pytest.raises(DecisionCooldownActive):
        asyncio.run(
            orchestrator.execute(
                match_id="m1",
                trigger="MOMENTUM_SHIFT",
                event_time=110,
                slot="winner",
                tenant_id="tenant-a",
                feature_snapshot={"home_xg": 1.3},
                now=120,
            )
        )
