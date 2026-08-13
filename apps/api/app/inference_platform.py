from __future__ import annotations

from dataclasses import dataclass
import asyncio
import hashlib
import json
import time
from typing import Awaitable, Callable


@dataclass(frozen=True)
class InferenceRequest:
    request_id: str
    tenant_id: str
    slot: str
    entity_id: str
    features: dict
    explain: bool
    latency_class: str


@dataclass(frozen=True)
class InferenceResult:
    request_id: str
    model_id: str
    prediction: float
    confidence: float
    cached: bool
    fallback_used: bool
    latency_ms: float
    explanation: dict | None


@dataclass(frozen=True)
class WarmupState:
    model_id: str
    status: str
    attempts: int
    warmed_at: int | None
    detail: str


class InferenceTimeout(RuntimeError):
    pass


class ModelNotReady(RuntimeError):
    pass


class InMemoryModelRuntime:
    def __init__(
        self,
        *,
        model_id: str,
        weight: float = 1.0,
        bias: float = 0.0,
        delay_seconds: float = 0.0,
    ):
        self.model_id = model_id
        self.weight = weight
        self.bias = bias
        self.delay_seconds = delay_seconds
        self.ready = False

    async def warmup(self) -> None:
        await asyncio.sleep(0)
        self.ready = True

    async def predict(self, features: dict) -> float:
        if not self.ready:
            raise ModelNotReady(
                f"Model hazır değil: {self.model_id}"
            )
        if self.delay_seconds > 0:
            await asyncio.sleep(self.delay_seconds)

        values = [
            float(value)
            for value in features.values()
            if isinstance(value, (int, float))
            and not isinstance(value, bool)
        ]
        mean_value = (
            sum(values) / len(values)
            if values
            else 0.0
        )
        raw = (
            mean_value * self.weight
            + self.bias
        )
        return max(0.0, min(1.0, raw))


class ModelRuntimeRegistry:
    def __init__(self):
        self._runtimes = {}
        self._warmup = {}

    def register(self, runtime) -> None:
        self._runtimes[runtime.model_id] = runtime
        self._warmup[runtime.model_id] = WarmupState(
            model_id=runtime.model_id,
            status="COLD",
            attempts=0,
            warmed_at=None,
            detail="Model henüz warm-up olmadı",
        )

    def get(self, model_id: str):
        runtime = self._runtimes.get(model_id)
        if runtime is None:
            raise KeyError("Model runtime bulunamadı")
        return runtime

    async def warmup(self, model_id: str) -> WarmupState:
        runtime = self.get(model_id)
        current = self._warmup[model_id]
        attempts = current.attempts + 1
        try:
            await runtime.warmup()
            state = WarmupState(
                model_id=model_id,
                status="READY",
                attempts=attempts,
                warmed_at=int(time.time()),
                detail="Warm-up başarılı",
            )
        except Exception as exc:
            state = WarmupState(
                model_id=model_id,
                status="FAILED",
                attempts=attempts,
                warmed_at=None,
                detail=str(exc),
            )
        self._warmup[model_id] = state
        return state

    def status(self, model_id: str) -> WarmupState:
        if model_id not in self._warmup:
            raise KeyError("Model runtime bulunamadı")
        return self._warmup[model_id]


class RedisPredictionCache:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:prediction-cache",
        ttl_seconds: int = 30,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def make_key(
        self,
        *,
        tenant_id: str,
        model_id: str,
        features: dict,
    ) -> str:
        canonical = json.dumps(
            features,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        )
        digest = hashlib.sha256(
            canonical.encode("utf-8")
        ).hexdigest()
        return (
            f"{self.prefix}:{tenant_id}:"
            f"{model_id}:{digest}"
        )

    def get(self, key: str) -> dict | None:
        payload = self.client.get(key)
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return json.loads(payload)

    def set(self, key: str, value: dict) -> None:
        self.client.setex(
            key,
            self.ttl_seconds,
            json.dumps(
                value,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )


class AdaptiveInferenceRouter:
    def __init__(
        self,
        *,
        deployment_manager,
    ):
        self.deployment_manager = deployment_manager

    def route(self, request: InferenceRequest) -> tuple[str, str | None]:
        state = self.deployment_manager.get(
            request.slot
        )
        if state.champion_model_id is None:
            raise RuntimeError(
                "Slot için champion model bulunamadı"
            )

        primary = state.champion_model_id
        fallback = state.previous_champion_model_id

        if (
            request.latency_class == "BATCH"
            and state.challenger_model_id is not None
        ):
            primary = state.challenger_model_id

        return primary, fallback


class InferenceService:
    def __init__(
        self,
        *,
        runtime_registry,
        router,
        cache,
        timeout_seconds: float = 1.0,
    ):
        self.runtime_registry = runtime_registry
        self.router = router
        self.cache = cache
        self.timeout_seconds = timeout_seconds

    async def infer(
        self,
        request: InferenceRequest,
    ) -> InferenceResult:
        primary_model_id, fallback_model_id = (
            self.router.route(request)
        )

        cached = self._cache_lookup(
            request,
            primary_model_id,
        )
        if cached is not None:
            return InferenceResult(
                request_id=request.request_id,
                model_id=primary_model_id,
                prediction=float(
                    cached["prediction"]
                ),
                confidence=float(
                    cached["confidence"]
                ),
                cached=True,
                fallback_used=False,
                latency_ms=0.0,
                explanation=cached.get(
                    "explanation"
                ),
            )

        started = time.perf_counter()
        fallback_used = False
        model_id = primary_model_id

        try:
            prediction = await self._predict(
                model_id,
                request.features,
            )
        except (
            asyncio.TimeoutError,
            ModelNotReady,
            KeyError,
        ) as exc:
            if fallback_model_id is None:
                raise InferenceTimeout(
                    "Inference başarısız ve fallback yok"
                ) from exc
            fallback_used = True
            model_id = fallback_model_id
            prediction = await self._predict(
                model_id,
                request.features,
            )

        latency_ms = (
            time.perf_counter() - started
        ) * 1000
        confidence = round(
            1.0 - abs(0.5 - prediction),
            6,
        )
        explanation = (
            self._explain(
                request.features,
                prediction,
            )
            if request.explain
            else None
        )

        result_payload = {
            "prediction": prediction,
            "confidence": confidence,
            "explanation": explanation,
        }
        self.cache.set(
            self.cache.make_key(
                tenant_id=request.tenant_id,
                model_id=model_id,
                features=request.features,
            ),
            result_payload,
        )

        return InferenceResult(
            request_id=request.request_id,
            model_id=model_id,
            prediction=round(prediction, 6),
            confidence=confidence,
            cached=False,
            fallback_used=fallback_used,
            latency_ms=round(
                latency_ms,
                3,
            ),
            explanation=explanation,
        )

    async def _predict(
        self,
        model_id: str,
        features: dict,
    ) -> float:
        runtime = self.runtime_registry.get(
            model_id
        )
        return await asyncio.wait_for(
            runtime.predict(features),
            timeout=self.timeout_seconds,
        )

    def _cache_lookup(
        self,
        request: InferenceRequest,
        model_id: str,
    ) -> dict | None:
        return self.cache.get(
            self.cache.make_key(
                tenant_id=request.tenant_id,
                model_id=model_id,
                features=request.features,
            )
        )

    @staticmethod
    def _explain(
        features: dict,
        prediction: float,
    ) -> dict:
        numeric = [
            (
                name,
                abs(float(value)),
            )
            for name, value in features.items()
            if isinstance(value, (int, float))
            and not isinstance(value, bool)
        ]
        numeric.sort(
            key=lambda item: item[1],
            reverse=True,
        )
        return {
            "prediction": round(
                prediction,
                6,
            ),
            "top_features": [
                {
                    "name": name,
                    "importance": round(
                        importance,
                        6,
                    ),
                }
                for name, importance in numeric[:5]
            ],
        }


class MicroBatcher:
    def __init__(
        self,
        *,
        service,
        max_batch_size: int = 16,
    ):
        if max_batch_size < 1:
            raise ValueError(
                "max_batch_size en az 1 olmalıdır"
            )
        self.service = service
        self.max_batch_size = max_batch_size

    async def infer_many(
        self,
        requests: tuple[InferenceRequest, ...],
    ) -> tuple[InferenceResult, ...]:
        results = []
        for index in range(
            0,
            len(requests),
            self.max_batch_size,
        ):
            chunk = requests[
                index:index + self.max_batch_size
            ]
            chunk_results = await asyncio.gather(
                *[
                    self.service.infer(request)
                    for request in chunk
                ]
            )
            results.extend(chunk_results)
        return tuple(results)
