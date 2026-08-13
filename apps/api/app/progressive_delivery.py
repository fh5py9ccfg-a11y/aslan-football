from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class ProgressiveDeliveryPlan:
    plan_id: str
    tenant_id: str
    release_id: str
    stages: tuple[int, ...]
    minimum_reliability_score: int
    max_warning_slos: int
    max_critical_slos: int
    observation_window_seconds: int
    auto_rollback: bool
    created_at: int


@dataclass(frozen=True)
class ProgressiveDeliveryState:
    plan_id: str
    release_id: str
    current_stage_index: int
    current_percentage: int
    status: str
    last_reliability_score: int | None
    last_warning_slos: int
    last_critical_slos: int
    rollback_reason: str | None
    updated_at: int


@dataclass(frozen=True)
class RolloutEvaluation:
    evaluation_id: str
    plan_id: str
    release_id: str
    stage_percentage: int
    reliability_score: int
    warning_slos: int
    critical_slos: int
    action: str
    reason: str
    evaluated_at: int


class ProgressiveDeliveryValidationError(ValueError):
    pass


class RedisProgressiveDeliveryRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:progressive-delivery",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_plan(
        self,
        plan: ProgressiveDeliveryPlan,
    ) -> ProgressiveDeliveryPlan:
        payload = {
            **plan.__dict__,
            "stages": list(plan.stages),
        }
        self.client.setex(
            self._plan_key(plan.plan_id),
            self.ttl_seconds,
            json.dumps(
                payload,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._tenant_plan_index(plan.tenant_id),
            plan.plan_id,
        )
        return plan

    def get_plan(
        self,
        plan_id: str,
    ) -> ProgressiveDeliveryPlan | None:
        payload = self.client.get(
            self._plan_key(plan_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["stages"] = tuple(data["stages"])
        return ProgressiveDeliveryPlan(**data)

    def save_state(
        self,
        state: ProgressiveDeliveryState,
    ) -> ProgressiveDeliveryState:
        self.client.setex(
            self._state_key(state.plan_id),
            self.ttl_seconds,
            json.dumps(
                state.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        return state

    def get_state(
        self,
        plan_id: str,
    ) -> ProgressiveDeliveryState | None:
        payload = self.client.get(
            self._state_key(plan_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ProgressiveDeliveryState(
            **json.loads(payload)
        )

    def save_evaluation(
        self,
        evaluation: RolloutEvaluation,
    ) -> RolloutEvaluation:
        self.client.setex(
            self._evaluation_key(
                evaluation.evaluation_id
            ),
            self.ttl_seconds,
            json.dumps(
                evaluation.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._evaluation_index(
                evaluation.plan_id
            ),
            evaluation.evaluation_id,
        )
        return evaluation

    def list_evaluations(
        self,
        plan_id: str,
        *,
        limit: int = 100,
    ) -> tuple[RolloutEvaluation, ...]:
        items = []
        for evaluation_id in self.client.smembers(
            self._evaluation_index(plan_id)
        ):
            if isinstance(evaluation_id, bytes):
                evaluation_id = (
                    evaluation_id.decode("utf-8")
                )
            payload = self.client.get(
                self._evaluation_key(
                    str(evaluation_id)
                )
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                RolloutEvaluation(**json.loads(payload))
            )
        items.sort(
            key=lambda item: item.evaluated_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def _plan_key(self, plan_id: str) -> str:
        return f"{self.prefix}:plan:{plan_id}"

    def _tenant_plan_index(
        self,
        tenant_id: str,
    ) -> str:
        return f"{self.prefix}:plans:{tenant_id}"

    def _state_key(self, plan_id: str) -> str:
        return f"{self.prefix}:state:{plan_id}"

    def _evaluation_key(
        self,
        evaluation_id: str,
    ) -> str:
        return (
            f"{self.prefix}:evaluation:"
            f"{evaluation_id}"
        )

    def _evaluation_index(
        self,
        plan_id: str,
    ) -> str:
        return (
            f"{self.prefix}:evaluations:"
            f"{plan_id}"
        )


class ProgressiveDeliveryService:
    def __init__(
        self,
        *,
        repository,
        reliability_service,
        release_guard_service,
    ):
        self.repository = repository
        self.reliability_service = (
            reliability_service
        )
        self.release_guard_service = (
            release_guard_service
        )

    def create_plan(
        self,
        *,
        plan_id: str,
        tenant_id: str,
        release_id: str,
        stages: tuple[int, ...],
        minimum_reliability_score: int = 70,
        max_warning_slos: int = 0,
        max_critical_slos: int = 0,
        observation_window_seconds: int = 300,
        auto_rollback: bool = True,
        now: int | None = None,
    ) -> ProgressiveDeliveryPlan:
        self._validate_stages(stages)

        if not 0 <= minimum_reliability_score <= 100:
            raise ProgressiveDeliveryValidationError(
                "Minimum reliability score 0 ile 100 arasında olmalıdır"
            )
        if max_warning_slos < 0 or max_critical_slos < 0:
            raise ProgressiveDeliveryValidationError(
                "SLO limitleri negatif olamaz"
            )
        if observation_window_seconds < 30:
            raise ProgressiveDeliveryValidationError(
                "Observation window en az 30 saniye olmalıdır"
            )

        current = int(
            now if now is not None
            else time.time()
        )
        plan = ProgressiveDeliveryPlan(
            plan_id=plan_id,
            tenant_id=tenant_id,
            release_id=release_id,
            stages=stages,
            minimum_reliability_score=(
                minimum_reliability_score
            ),
            max_warning_slos=max_warning_slos,
            max_critical_slos=max_critical_slos,
            observation_window_seconds=(
                observation_window_seconds
            ),
            auto_rollback=auto_rollback,
            created_at=current,
        )
        self.repository.save_plan(plan)
        self.repository.save_state(
            ProgressiveDeliveryState(
                plan_id=plan_id,
                release_id=release_id,
                current_stage_index=0,
                current_percentage=stages[0],
                status="READY",
                last_reliability_score=None,
                last_warning_slos=0,
                last_critical_slos=0,
                rollback_reason=None,
                updated_at=current,
            )
        )
        return plan

    def start(
        self,
        *,
        plan_id: str,
        gate_decision_id: str,
        now: int | None = None,
    ) -> ProgressiveDeliveryState:
        plan = self._required_plan(plan_id)
        gate = self.release_guard_service.evaluate(
            decision_id=gate_decision_id,
            tenant_id=plan.tenant_id,
            release_id=plan.release_id,
            now=now,
        )
        if not gate.allowed:
            raise RuntimeError(
                f"Release guard rollout başlangıcını engelledi: {gate.reason}"
            )

        current = int(
            now if now is not None
            else time.time()
        )
        state = ProgressiveDeliveryState(
            plan_id=plan.plan_id,
            release_id=plan.release_id,
            current_stage_index=0,
            current_percentage=plan.stages[0],
            status="RUNNING",
            last_reliability_score=(
                gate.reliability_score
            ),
            last_warning_slos=gate.warning_slos,
            last_critical_slos=gate.critical_slos,
            rollback_reason=None,
            updated_at=current,
        )
        return self.repository.save_state(state)

    def evaluate(
        self,
        *,
        plan_id: str,
        evaluation_id: str,
        now: int | None = None,
    ) -> tuple[
        ProgressiveDeliveryState,
        RolloutEvaluation,
    ]:
        plan = self._required_plan(plan_id)
        state = self._required_state(plan_id)

        if state.status not in {
            "RUNNING",
            "PAUSED",
        }:
            raise RuntimeError(
                "Rollout değerlendirmeye açık değil"
            )

        current = int(
            now if now is not None
            else time.time()
        )
        reliability = (
            self.reliability_service
            .reliability_score(
                tenant_id=plan.tenant_id,
                now=now,
            )
        )

        score = int(reliability["score"])
        warning = int(
            reliability.get("warning_slos", 0)
        )
        critical = int(
            reliability.get("critical_slos", 0)
        )

        violations = []
        if score < plan.minimum_reliability_score:
            violations.append(
                "Reliability score rollout eşiğinin altında"
            )
        if warning > plan.max_warning_slos:
            violations.append(
                "Warning SLO limiti aşıldı"
            )
        if critical > plan.max_critical_slos:
            violations.append(
                "Critical SLO limiti aşıldı"
            )

        if violations:
            action = (
                "ROLLBACK"
                if plan.auto_rollback
                else "PAUSE"
            )
            status = (
                "ROLLED_BACK"
                if plan.auto_rollback
                else "PAUSED"
            )
            reason = "; ".join(violations)
            next_state = ProgressiveDeliveryState(
                **{
                    **state.__dict__,
                    "status": status,
                    "last_reliability_score": score,
                    "last_warning_slos": warning,
                    "last_critical_slos": critical,
                    "rollback_reason": (
                        reason
                        if plan.auto_rollback
                        else None
                    ),
                    "updated_at": current,
                }
            )
        elif (
            state.current_stage_index
            >= len(plan.stages) - 1
        ):
            action = "COMPLETE"
            reason = (
                "Son canary aşaması kalite "
                "kapılarını geçti"
            )
            next_state = ProgressiveDeliveryState(
                **{
                    **state.__dict__,
                    "status": "COMPLETED",
                    "last_reliability_score": score,
                    "last_warning_slos": warning,
                    "last_critical_slos": critical,
                    "updated_at": current,
                }
            )
        else:
            next_index = (
                state.current_stage_index + 1
            )
            action = "PROMOTE"
            reason = (
                "Canary aşaması kalite "
                "kapılarını geçti"
            )
            next_state = ProgressiveDeliveryState(
                plan_id=state.plan_id,
                release_id=state.release_id,
                current_stage_index=next_index,
                current_percentage=(
                    plan.stages[next_index]
                ),
                status="RUNNING",
                last_reliability_score=score,
                last_warning_slos=warning,
                last_critical_slos=critical,
                rollback_reason=None,
                updated_at=current,
            )

        evaluation = RolloutEvaluation(
            evaluation_id=evaluation_id,
            plan_id=plan.plan_id,
            release_id=plan.release_id,
            stage_percentage=(
                state.current_percentage
            ),
            reliability_score=score,
            warning_slos=warning,
            critical_slos=critical,
            action=action,
            reason=reason,
            evaluated_at=current,
        )
        self.repository.save_evaluation(
            evaluation
        )
        self.repository.save_state(next_state)
        return next_state, evaluation

    def resume(
        self,
        *,
        plan_id: str,
        now: int | None = None,
    ) -> ProgressiveDeliveryState:
        state = self._required_state(plan_id)
        if state.status != "PAUSED":
            raise RuntimeError(
                "Yalnızca paused rollout devam ettirilebilir"
            )
        updated = ProgressiveDeliveryState(
            **{
                **state.__dict__,
                "status": "RUNNING",
                "updated_at": int(
                    now if now is not None
                    else time.time()
                ),
            }
        )
        return self.repository.save_state(updated)

    @staticmethod
    def _validate_stages(
        stages: tuple[int, ...],
    ) -> None:
        if not stages:
            raise ProgressiveDeliveryValidationError(
                "En az bir rollout aşaması gereklidir"
            )
        if stages[-1] != 100:
            raise ProgressiveDeliveryValidationError(
                "Son rollout aşaması 100 olmalıdır"
            )
        if any(
            item <= 0 or item > 100
            for item in stages
        ):
            raise ProgressiveDeliveryValidationError(
                "Rollout yüzdeleri 1 ile 100 arasında olmalıdır"
            )
        if tuple(sorted(set(stages))) != stages:
            raise ProgressiveDeliveryValidationError(
                "Rollout aşamaları artan ve benzersiz olmalıdır"
            )

    def _required_plan(
        self,
        plan_id: str,
    ) -> ProgressiveDeliveryPlan:
        plan = self.repository.get_plan(plan_id)
        if plan is None:
            raise KeyError(
                "Progressive delivery plan bulunamadı"
            )
        return plan

    def _required_state(
        self,
        plan_id: str,
    ) -> ProgressiveDeliveryState:
        state = self.repository.get_state(plan_id)
        if state is None:
            raise KeyError(
                "Progressive delivery state bulunamadı"
            )
        return state
