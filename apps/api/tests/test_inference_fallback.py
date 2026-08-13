import asyncio

from apps.api.app.inference_platform import (
    AdaptiveInferenceRouter,
    InferenceRequest,
    InferenceService,
    InMemoryModelRuntime,
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
    champion_model_id = "slow"
    previous_champion_model_id = "fallback"
    challenger_model_id = None


class DeploymentManager:
    def get(self, slot):
        return Deployment()


def test_timeout_uses_fallback():
    registry = ModelRuntimeRegistry()
    registry.register(
        InMemoryModelRuntime(
            model_id="slow",
            delay_seconds=0.05,
        )
    )
    registry.register(
        InMemoryModelRuntime(
            model_id="fallback",
            weight=0.5,
        )
    )
    asyncio.run(registry.warmup("slow"))
    asyncio.run(registry.warmup("fallback"))

    service = InferenceService(
        runtime_registry=registry,
        router=AdaptiveInferenceRouter(
            deployment_manager=DeploymentManager()
        ),
        cache=RedisPredictionCache(
            Redis(),
            prefix="cache",
        ),
        timeout_seconds=0.01,
    )

    result = asyncio.run(
        service.infer(
            InferenceRequest(
                request_id="r1",
                tenant_id="tenant-a",
                slot="winner",
                entity_id="match-1",
                features={"form": 0.8},
                explain=False,
                latency_class="REALTIME",
            )
        )
    )

    assert result.fallback_used is True
    assert result.model_id == "fallback"
