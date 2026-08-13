from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class ReleaseGuardPolicy:
    policy_id: str
    tenant_id: str
    minimum_reliability_score: int
    block_on_warning: bool
    block_on_critical: bool
    require_override_reason: bool
    enabled: bool
    created_at: int


@dataclass(frozen=True)
class ReleaseGateDecision:
    decision_id: str
    tenant_id: str
    release_id: str
    reliability_score: int
    reliability_status: str
    warning_slos: int
    critical_slos: int
    allowed: bool
    reason: str
    overridden: bool
    override_actor: str | None
    override_reason: str | None
    evaluated_at: int


class ReleaseGuardValidationError(ValueError):
    pass


class RedisReleaseGuardRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:release-guard",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_policy(
        self,
        policy: ReleaseGuardPolicy,
    ) -> ReleaseGuardPolicy:
        self.client.setex(
            self._policy_key(policy.tenant_id),
            self.ttl_seconds,
            json.dumps(
                policy.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        return policy

    def get_policy(
        self,
        tenant_id: str,
    ) -> ReleaseGuardPolicy | None:
        payload = self.client.get(
            self._policy_key(tenant_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ReleaseGuardPolicy(**json.loads(payload))

    def save_decision(
        self,
        decision: ReleaseGateDecision,
    ) -> ReleaseGateDecision:
        self.client.setex(
            self._decision_key(decision.decision_id),
            self.ttl_seconds,
            json.dumps(
                decision.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._decision_index(decision.tenant_id),
            decision.decision_id,
        )
        return decision

    def list_decisions(
        self,
        tenant_id: str,
        *,
        limit: int = 100,
    ) -> tuple[ReleaseGateDecision, ...]:
        items = []
        for decision_id in self.client.smembers(
            self._decision_index(tenant_id)
        ):
            if isinstance(decision_id, bytes):
                decision_id = decision_id.decode("utf-8")
            payload = self.client.get(
                self._decision_key(str(decision_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                ReleaseGateDecision(**json.loads(payload))
            )
        items.sort(
            key=lambda item: item.evaluated_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def _policy_key(self, tenant_id: str) -> str:
        return f"{self.prefix}:policy:{tenant_id}"

    def _decision_key(self, decision_id: str) -> str:
        return f"{self.prefix}:decision:{decision_id}"

    def _decision_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:decisions:{tenant_id}"


class ReleaseGuardService:
    def __init__(
        self,
        *,
        repository,
        reliability_service,
    ):
        self.repository = repository
        self.reliability_service = reliability_service

    def create_policy(
        self,
        *,
        policy_id: str,
        tenant_id: str,
        minimum_reliability_score: int = 70,
        block_on_warning: bool = False,
        block_on_critical: bool = True,
        require_override_reason: bool = True,
        now: int | None = None,
    ) -> ReleaseGuardPolicy:
        if not 0 <= minimum_reliability_score <= 100:
            raise ReleaseGuardValidationError(
                "Minimum reliability score 0 ile 100 arasında olmalıdır"
            )

        policy = ReleaseGuardPolicy(
            policy_id=policy_id,
            tenant_id=tenant_id,
            minimum_reliability_score=minimum_reliability_score,
            block_on_warning=block_on_warning,
            block_on_critical=block_on_critical,
            require_override_reason=require_override_reason,
            enabled=True,
            created_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_policy(policy)

    def evaluate(
        self,
        *,
        decision_id: str,
        tenant_id: str,
        release_id: str,
        override_actor: str | None = None,
        override_reason: str | None = None,
        now: int | None = None,
    ) -> ReleaseGateDecision:
        policy = self.repository.get_policy(tenant_id)
        if policy is None:
            policy = self.create_policy(
                policy_id=f"default:{tenant_id}",
                tenant_id=tenant_id,
                now=now,
            )

        reliability = self.reliability_service.reliability_score(
            tenant_id=tenant_id,
            now=now,
        )

        reasons = []
        if reliability["score"] < policy.minimum_reliability_score:
            reasons.append(
                "Reliability score minimum eşiğin altında"
            )
        if (
            policy.block_on_critical
            and reliability.get("critical_slos", 0) > 0
        ):
            reasons.append(
                "Kritik error-budget ihlali mevcut"
            )
        if (
            policy.block_on_warning
            and reliability.get("warning_slos", 0) > 0
        ):
            reasons.append(
                "Warning seviyesinde error-budget ihlali mevcut"
            )

        blocked = bool(reasons)
        overridden = override_actor is not None

        if overridden and policy.require_override_reason:
            if not override_reason or len(override_reason.strip()) < 5:
                raise ReleaseGuardValidationError(
                    "Override için açıklayıcı neden gereklidir"
                )

        allowed = not blocked or overridden
        if not reasons:
            reason = "Release gate başarıyla geçti"
        elif overridden:
            reason = "Release gate yetkili override ile açıldı"
        else:
            reason = "; ".join(reasons)

        decision = ReleaseGateDecision(
            decision_id=decision_id,
            tenant_id=tenant_id,
            release_id=release_id,
            reliability_score=int(reliability["score"]),
            reliability_status=str(reliability["status"]),
            warning_slos=int(
                reliability.get("warning_slos", 0)
            ),
            critical_slos=int(
                reliability.get("critical_slos", 0)
            ),
            allowed=allowed,
            reason=reason,
            overridden=overridden,
            override_actor=override_actor,
            override_reason=override_reason,
            evaluated_at=int(
                now if now is not None
                else time.time()
            ),
        )
        return self.repository.save_decision(decision)
