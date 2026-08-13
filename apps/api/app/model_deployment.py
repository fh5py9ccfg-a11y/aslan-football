from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class ModelDeploymentState:
    slot: str
    champion_model_id: str | None
    previous_champion_model_id: str | None
    challenger_model_id: str | None
    rollout_percent: int
    status: str
    generation: int
    updated_at: int


class ModelDeploymentManager:
    def __init__(
        self,
        client,
        *,
        registry,
        prefix: str = "aslan:model-deployment",
    ):
        self.client = client
        self.registry = registry
        self.prefix = prefix

    def get(
        self,
        slot: str,
    ) -> ModelDeploymentState:
        payload = self.client.get(self._key(slot))
        if payload is None:
            return ModelDeploymentState(
                slot=slot,
                champion_model_id=None,
                previous_champion_model_id=None,
                challenger_model_id=None,
                rollout_percent=0,
                status="EMPTY",
                generation=0,
                updated_at=0,
            )
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ModelDeploymentState(**json.loads(payload))

    def assign_champion(
        self,
        *,
        slot: str,
        model_id: str,
        now: int | None = None,
    ) -> ModelDeploymentState:
        self.registry.required(model_id)
        current = self.get(slot)
        timestamp = int(
            now if now is not None
            else time.time()
        )
        updated = ModelDeploymentState(
            slot=slot,
            champion_model_id=model_id,
            previous_champion_model_id=(
                current.champion_model_id
            ),
            challenger_model_id=None,
            rollout_percent=100,
            status="STABLE",
            generation=current.generation + 1,
            updated_at=timestamp,
        )
        self.registry.update_status(
            model_id,
            status="CHAMPION",
            now=timestamp,
        )
        self._save(updated)
        return updated

    def start_challenger(
        self,
        *,
        slot: str,
        model_id: str,
        rollout_percent: int = 5,
        now: int | None = None,
    ) -> ModelDeploymentState:
        if not 1 <= rollout_percent <= 50:
            raise ValueError(
                "Challenger rollout 1 ile 50 arasında olmalıdır"
            )
        self.registry.required(model_id)
        current = self.get(slot)
        if current.champion_model_id is None:
            raise RuntimeError(
                "Önce champion model atanmalıdır"
            )

        timestamp = int(
            now if now is not None
            else time.time()
        )
        updated = ModelDeploymentState(
            slot=slot,
            champion_model_id=(
                current.champion_model_id
            ),
            previous_champion_model_id=(
                current.previous_champion_model_id
            ),
            challenger_model_id=model_id,
            rollout_percent=rollout_percent,
            status="CHALLENGER_RUNNING",
            generation=current.generation + 1,
            updated_at=timestamp,
        )
        self.registry.update_status(
            model_id,
            status="CHALLENGER",
            now=timestamp,
        )
        self._save(updated)
        return updated

    def promote_challenger(
        self,
        *,
        slot: str,
        now: int | None = None,
    ) -> ModelDeploymentState:
        current = self.get(slot)
        if current.challenger_model_id is None:
            raise RuntimeError(
                "Aktif challenger bulunamadı"
            )
        return self.assign_champion(
            slot=slot,
            model_id=current.challenger_model_id,
            now=now,
        )

    def rollback(
        self,
        *,
        slot: str,
        now: int | None = None,
    ) -> ModelDeploymentState:
        current = self.get(slot)
        if current.previous_champion_model_id is None:
            raise RuntimeError(
                "Rollback için önceki champion bulunamadı"
            )
        return self.assign_champion(
            slot=slot,
            model_id=(
                current.previous_champion_model_id
            ),
            now=now,
        )

    def _save(
        self,
        state: ModelDeploymentState,
    ) -> None:
        self.client.set(
            self._key(state.slot),
            json.dumps(
                state.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

    def _key(self, slot: str) -> str:
        return f"{self.prefix}:{slot}"
