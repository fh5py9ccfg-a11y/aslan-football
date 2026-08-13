from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class ModelRecord:
    model_id: str
    name: str
    version: str
    status: str
    framework: str
    artifact_uri: str
    artifact_sha256: str
    feature_version: str
    training_dataset: str
    created_at: int
    updated_at: int
    metadata: dict


class ModelRegistryConflict(RuntimeError):
    pass


class RedisModelRegistry:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:model-registry",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def register(
        self,
        *,
        model_id: str,
        name: str,
        version: str,
        framework: str,
        artifact_uri: str,
        artifact_sha256: str,
        feature_version: str,
        training_dataset: str,
        metadata: dict | None = None,
        now: int | None = None,
    ) -> ModelRecord:
        if len(artifact_sha256) != 64:
            raise ValueError(
                "Model artifact SHA-256 64 karakter olmalıdır"
            )
        if self.get(model_id) is not None:
            raise ModelRegistryConflict(
                "Model kimliği zaten kayıtlı"
            )

        current = int(now if now is not None else time.time())
        record = ModelRecord(
            model_id=model_id,
            name=name,
            version=version,
            status="REGISTERED",
            framework=framework,
            artifact_uri=artifact_uri,
            artifact_sha256=artifact_sha256,
            feature_version=feature_version,
            training_dataset=training_dataset,
            created_at=current,
            updated_at=current,
            metadata=metadata or {},
        )
        self._save(record)
        self.client.sadd(self._index_key(), model_id)
        return record

    def update_status(
        self,
        model_id: str,
        *,
        status: str,
        now: int | None = None,
    ) -> ModelRecord:
        record = self.required(model_id)
        current = int(now if now is not None else time.time())
        updated = ModelRecord(
            **{
                **record.__dict__,
                "status": status,
                "updated_at": current,
            }
        )
        self._save(updated)
        return updated

    def get(self, model_id: str) -> ModelRecord | None:
        payload = self.client.get(self._model_key(model_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ModelRecord(**json.loads(payload))

    def required(self, model_id: str) -> ModelRecord:
        record = self.get(model_id)
        if record is None:
            raise KeyError("Model kaydı bulunamadı")
        return record

    def list_models(self) -> tuple[ModelRecord, ...]:
        items = []
        for model_id in self.client.smembers(self._index_key()):
            if isinstance(model_id, bytes):
                model_id = model_id.decode("utf-8")
            record = self.get(str(model_id))
            if record is not None:
                items.append(record)
        items.sort(
            key=lambda item: (
                item.name,
                item.version,
            )
        )
        return tuple(items)

    def _save(self, record: ModelRecord) -> None:
        self.client.setex(
            self._model_key(record.model_id),
            self.ttl_seconds,
            json.dumps(
                record.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

    def _model_key(self, model_id: str) -> str:
        return f"{self.prefix}:model:{model_id}"

    def _index_key(self) -> str:
        return f"{self.prefix}:models"
