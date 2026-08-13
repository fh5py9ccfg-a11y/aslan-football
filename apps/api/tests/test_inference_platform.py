import asyncio

from apps.api.app.inference_platform import (
    AdaptiveInferenceRouter,
    InferenceRequest,
    InferenceService,
    InMemoryModelRuntime,
    MicroBatcher,
    ModelRuntimeRegistry,
    RedisPredictionCache,
)


class Redis:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value


class Deployment:
    champion_model_id = "m1"
    previous_champion_model_id = "m2"
    challenger_model_id = None


class DeploymentManager:
    def get(self, slot):
        return Deployment()


def request():
    return InferenceRequest(
        request_id="r1",
        tenant_id="tenant-a",
        slot="winner",
        entity_id="match-1",
        features={
            "form": 0.8,
            "xg": 0.6,
        },
        explain=True,
        latency_class="REALTIME",
    )


def build_service():
    registry = ModelRuntimeRegistry()
    registry.register(
        InMemoryModelRuntime(
            model_id="m1",
            weight=1.0,
        )
    )
    registry.register(
        InMemoryModelRuntime(
            model_id="m2",
            weight=0.5,
            bias=0.1,
        )
    )
    asyncio.run(registry.warmup("m1"))
    asyncio.run(registry.warmup("m2"))

    return InferenceService(
        runtime_registry=registry,
        router=AdaptiveInferenceRouter(
            deployment_manager=DeploymentManager()
        ),
        cache=RedisPredictionCache(
            Redis(),
            prefix="cache",
            ttl_seconds=30,
        ),
        timeout_seconds=0.1,
    )


def test_inference_and_cache():
    service = build_service()

    first = asyncio.run(service.infer(request()))
    second = asyncio.run(service.infer(request()))

    assert first.cached is False
    assert second.cached is True
    assert first.model_id == "m1"
    assert first.explanation is not None


def test_micro_batcher():
    service = build_service()
    batcher = MicroBatcher(
        service=service,
        max_batch_size=1,
    )

    results = asyncio.run(
        batcher.infer_many(
            (
                request(),
                InferenceRequest(
                    **{
                        **request().__dict__,
                        "request_id": "r2",
                        "entity_id": "match-2",
                        "features": {"form": 0.4},
                    }
                ),
            )
        )
    )

    assert len(results) == 2


def test_warmup_state():
    registry = ModelRuntimeRegistry()
    registry.register(
        InMemoryModelRuntime(
            model_id="m1"
        )
    )

    state = asyncio.run(
        registry.warmup("m1")
    )

    assert state.status == "READY"
    assert state.attempts == 1
