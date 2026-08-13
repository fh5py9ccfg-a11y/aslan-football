from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class NodeHealth:
    node_id: str
    region: str
    role: str
    status: str
    score: int
    cpu_percent: float
    memory_percent: float
    error_rate: float
    latency_ms: float
    heartbeat_at: int
    quarantined_until: int | None
    recovery_attempts: int
    updated_at: int


@dataclass(frozen=True)
class HealingAction:
    action_id: str
    node_id: str
    action: str
    reason: str
    status: str
    created_at: int
    completed_at: int | None


class NodeHealthScorer:
    @staticmethod
    def calculate(
        *,
        cpu_percent: float,
        memory_percent: float,
        error_rate: float,
        latency_ms: float,
    ) -> int:
        cpu_penalty = max(0.0, cpu_percent - 65.0) * 0.8
        memory_penalty = max(0.0, memory_percent - 70.0) * 0.9
        error_penalty = max(0.0, error_rate) * 180.0
        latency_penalty = max(0.0, latency_ms - 250.0) / 12.0
        score = 100.0 - (
            cpu_penalty
            + memory_penalty
            + error_penalty
            + latency_penalty
        )
        return int(max(0, min(100, round(score))))


class RedisSelfHealingRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:self-healing",
        ttl_seconds: int = 604800,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_node(self, node: NodeHealth) -> NodeHealth:
        self.client.setex(
            self._node_key(node.node_id),
            self.ttl_seconds,
            self._serialize(node),
        )
        self.client.sadd(self._node_index(), node.node_id)
        return node

    def get_node(self, node_id: str) -> NodeHealth | None:
        payload = self.client.get(self._node_key(node_id))
        if payload is None:
            return None
        return self._deserialize_node(payload)

    def list_nodes(self) -> tuple[NodeHealth, ...]:
        items = []
        for node_id in self.client.smembers(self._node_index()):
            if isinstance(node_id, bytes):
                node_id = node_id.decode("utf-8")
            node = self.get_node(str(node_id))
            if node is not None:
                items.append(node)
        return tuple(sorted(items, key=lambda item: item.node_id))

    def save_action(self, action: HealingAction) -> HealingAction:
        self.client.setex(
            self._action_key(action.action_id),
            self.ttl_seconds,
            self._serialize(action),
        )
        self.client.sadd(self._action_index(), action.action_id)
        return action

    def list_actions(self, *, limit: int = 100) -> tuple[HealingAction, ...]:
        items = []
        for action_id in self.client.smembers(self._action_index()):
            if isinstance(action_id, bytes):
                action_id = action_id.decode("utf-8")
            payload = self.client.get(self._action_key(str(action_id)))
            if payload is not None:
                items.append(self._deserialize_action(payload))
        items.sort(key=lambda item: item.created_at, reverse=True)
        return tuple(items[:limit])

    def _node_key(self, node_id: str) -> str:
        return f"{self.prefix}:node:{node_id}"

    def _node_index(self) -> str:
        return f"{self.prefix}:nodes"

    def _action_key(self, action_id: str) -> str:
        return f"{self.prefix}:action:{action_id}"

    def _action_index(self) -> str:
        return f"{self.prefix}:actions"

    @staticmethod
    def _serialize(item) -> str:
        return json.dumps(
            item.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize_node(payload) -> NodeHealth:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return NodeHealth(**json.loads(payload))

    @staticmethod
    def _deserialize_action(payload) -> HealingAction:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return HealingAction(**json.loads(payload))


class SelfHealingOrchestrator:
    def __init__(
        self,
        *,
        repository,
        heartbeat_timeout_seconds: int = 60,
        quarantine_seconds: int = 300,
        unhealthy_score: int = 35,
        degraded_score: int = 65,
    ):
        self.repository = repository
        self.heartbeat_timeout_seconds = heartbeat_timeout_seconds
        self.quarantine_seconds = quarantine_seconds
        self.unhealthy_score = unhealthy_score
        self.degraded_score = degraded_score

    def report(
        self,
        *,
        node_id: str,
        region: str,
        role: str,
        cpu_percent: float,
        memory_percent: float,
        error_rate: float,
        latency_ms: float,
        now: int | None = None,
    ) -> NodeHealth:
        current = int(now if now is not None else time.time())
        score = NodeHealthScorer.calculate(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            error_rate=error_rate,
            latency_ms=latency_ms,
        )
        existing = self.repository.get_node(node_id)
        quarantined_until = (
            existing.quarantined_until if existing is not None else None
        )
        recovery_attempts = (
            existing.recovery_attempts if existing is not None else 0
        )

        if quarantined_until is not None and quarantined_until > current:
            status = "QUARANTINED"
        elif score < self.unhealthy_score:
            status = "UNHEALTHY"
        elif score < self.degraded_score:
            status = "DEGRADED"
        else:
            status = "HEALTHY"

        node = NodeHealth(
            node_id=node_id,
            region=region,
            role=role,
            status=status,
            score=score,
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            error_rate=error_rate,
            latency_ms=latency_ms,
            heartbeat_at=current,
            quarantined_until=quarantined_until,
            recovery_attempts=recovery_attempts,
            updated_at=current,
        )
        return self.repository.save_node(node)

    def reconcile(self, *, now: int | None = None) -> tuple[HealingAction, ...]:
        current = int(now if now is not None else time.time())
        actions = []

        for node in self.repository.list_nodes():
            stale = (
                current - node.heartbeat_at
                > self.heartbeat_timeout_seconds
            )

            if stale and node.status != "QUARANTINED":
                actions.append(
                    self._quarantine(
                        node,
                        reason="Heartbeat timeout",
                        now=current,
                    )
                )
                continue

            if node.status == "UNHEALTHY" and node.quarantined_until is None:
                actions.append(
                    self._quarantine(
                        node,
                        reason=f"Health score kritik: {node.score}",
                        now=current,
                    )
                )
                continue

            if (
                node.status == "QUARANTINED"
                and node.quarantined_until is not None
                and node.quarantined_until <= current
            ):
                actions.append(self._probe(node, now=current))

        return tuple(actions)

    def _quarantine(
        self,
        node: NodeHealth,
        *,
        reason: str,
        now: int,
    ) -> HealingAction:
        updated = NodeHealth(
            **{
                **node.__dict__,
                "status": "QUARANTINED",
                "quarantined_until": now + self.quarantine_seconds,
                "recovery_attempts": node.recovery_attempts + 1,
                "updated_at": now,
            }
        )
        self.repository.save_node(updated)
        return self.repository.save_action(
            HealingAction(
                action_id=(
                    f"{node.node_id}:quarantine:"
                    f"{updated.recovery_attempts}"
                ),
                node_id=node.node_id,
                action="QUARANTINE",
                reason=reason,
                status="COMPLETED",
                created_at=now,
                completed_at=now,
            )
        )

    def _probe(self, node: NodeHealth, *, now: int) -> HealingAction:
        recovered = node.score >= self.degraded_score
        updated = NodeHealth(
            **{
                **node.__dict__,
                "status": "HEALTHY" if recovered else "UNHEALTHY",
                "quarantined_until": None,
                "updated_at": now,
            }
        )
        self.repository.save_node(updated)
        return self.repository.save_action(
            HealingAction(
                action_id=(
                    f"{node.node_id}:probe:"
                    f"{node.recovery_attempts}"
                ),
                node_id=node.node_id,
                action="REJOIN" if recovered else "PROBE_FAILED",
                reason=(
                    "Node sağlıklı biçimde kümeye döndü"
                    if recovered
                    else "Node sağlık probe başarısız"
                ),
                status="COMPLETED",
                created_at=now,
                completed_at=now,
            )
        )

    def cluster_health(self) -> dict:
        nodes = self.repository.list_nodes()
        counts = {}
        for node in nodes:
            counts[node.status] = counts.get(node.status, 0) + 1

        healthy_nodes = sum(
            1 for node in nodes if node.status == "HEALTHY"
        )
        total = len(nodes)
        score = (
            int(round(sum(node.score for node in nodes) / total))
            if total
            else 0
        )
        return {
            "total_nodes": total,
            "healthy_nodes": healthy_nodes,
            "status_counts": counts,
            "cluster_score": score,
            "ready": total > 0 and healthy_nodes > 0,
        }
