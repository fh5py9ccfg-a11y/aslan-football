from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class ServiceLevelObjective:
    slo_id: str
    tenant_id: str
    service: str
    indicator: str
    target: float
    window_seconds: int
    warning_burn_rate: float
    critical_burn_rate: float
    enabled: bool
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class ReliabilityObservation:
    observation_id: str
    slo_id: str
    good_events: int
    total_events: int
    observed_at: int


@dataclass(frozen=True)
class ErrorBudgetSnapshot:
    slo_id: str
    service: str
    target: float
    achieved: float
    allowed_bad_events: float
    consumed_bad_events: int
    remaining_bad_events: float
    remaining_percent: float
    burn_rate: float
    status: str
    observed_events: int
    calculated_at: int


class ReliabilityValidationError(ValueError):
    pass


class RedisReliabilityRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:reliability",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_slo(
        self,
        slo: ServiceLevelObjective,
    ) -> ServiceLevelObjective:
        self.client.setex(
            self._slo_key(slo.slo_id),
            self.ttl_seconds,
            json.dumps(
                slo.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._tenant_slo_index(slo.tenant_id),
            slo.slo_id,
        )
        return slo

    def get_slo(
        self,
        slo_id: str,
    ) -> ServiceLevelObjective | None:
        payload = self.client.get(self._slo_key(slo_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ServiceLevelObjective(**json.loads(payload))

    def list_slos(
        self,
        tenant_id: str,
    ) -> tuple[ServiceLevelObjective, ...]:
        items = []
        for slo_id in self.client.smembers(
            self._tenant_slo_index(tenant_id)
        ):
            if isinstance(slo_id, bytes):
                slo_id = slo_id.decode("utf-8")
            item = self.get_slo(str(slo_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: (item.service, item.indicator))
        return tuple(items)

    def save_observation(
        self,
        observation: ReliabilityObservation,
    ) -> ReliabilityObservation:
        self.client.setex(
            self._observation_key(observation.observation_id),
            self.ttl_seconds,
            json.dumps(
                observation.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._observation_index(observation.slo_id),
            observation.observation_id,
        )
        return observation

    def list_observations(
        self,
        slo_id: str,
    ) -> tuple[ReliabilityObservation, ...]:
        items = []
        for observation_id in self.client.smembers(
            self._observation_index(slo_id)
        ):
            if isinstance(observation_id, bytes):
                observation_id = observation_id.decode("utf-8")
            payload = self.client.get(
                self._observation_key(str(observation_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                ReliabilityObservation(**json.loads(payload))
            )
        items.sort(key=lambda item: item.observed_at)
        return tuple(items)

    def save_snapshot(
        self,
        snapshot: ErrorBudgetSnapshot,
    ) -> ErrorBudgetSnapshot:
        self.client.setex(
            self._snapshot_key(snapshot.slo_id),
            self.ttl_seconds,
            json.dumps(
                snapshot.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        return snapshot

    def get_snapshot(
        self,
        slo_id: str,
    ) -> ErrorBudgetSnapshot | None:
        payload = self.client.get(
            self._snapshot_key(slo_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return ErrorBudgetSnapshot(**json.loads(payload))

    def _slo_key(self, slo_id: str) -> str:
        return f"{self.prefix}:slo:{slo_id}"

    def _tenant_slo_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:slos:{tenant_id}"

    def _observation_key(self, observation_id: str) -> str:
        return f"{self.prefix}:observation:{observation_id}"

    def _observation_index(self, slo_id: str) -> str:
        return f"{self.prefix}:observations:{slo_id}"

    def _snapshot_key(self, slo_id: str) -> str:
        return f"{self.prefix}:snapshot:{slo_id}"


class ReliabilityManagementService:
    def __init__(self, *, repository):
        self.repository = repository

    def create_slo(
        self,
        *,
        slo_id: str,
        tenant_id: str,
        service: str,
        indicator: str,
        target: float,
        window_seconds: int,
        warning_burn_rate: float = 1.0,
        critical_burn_rate: float = 2.0,
        now: int | None = None,
    ) -> ServiceLevelObjective:
        if not 0 < target < 1:
            raise ReliabilityValidationError(
                "SLO target 0 ile 1 arasında olmalıdır"
            )
        if window_seconds < 60:
            raise ReliabilityValidationError(
                "SLO penceresi en az 60 saniye olmalıdır"
            )
        if warning_burn_rate <= 0:
            raise ReliabilityValidationError(
                "Warning burn rate pozitif olmalıdır"
            )
        if critical_burn_rate <= warning_burn_rate:
            raise ReliabilityValidationError(
                "Critical burn rate warning değerinden büyük olmalıdır"
            )

        current = int(now if now is not None else time.time())
        slo = ServiceLevelObjective(
            slo_id=slo_id,
            tenant_id=tenant_id,
            service=service,
            indicator=indicator,
            target=target,
            window_seconds=window_seconds,
            warning_burn_rate=warning_burn_rate,
            critical_burn_rate=critical_burn_rate,
            enabled=True,
            created_at=current,
            updated_at=current,
        )
        return self.repository.save_slo(slo)

    def record(
        self,
        *,
        observation_id: str,
        slo_id: str,
        good_events: int,
        total_events: int,
        observed_at: int | None = None,
    ) -> ReliabilityObservation:
        if self.repository.get_slo(slo_id) is None:
            raise KeyError("SLO bulunamadı")
        if total_events <= 0:
            raise ReliabilityValidationError(
                "total_events pozitif olmalıdır"
            )
        if good_events < 0 or good_events > total_events:
            raise ReliabilityValidationError(
                "good_events 0 ile total_events arasında olmalıdır"
            )

        item = ReliabilityObservation(
            observation_id=observation_id,
            slo_id=slo_id,
            good_events=good_events,
            total_events=total_events,
            observed_at=int(
                observed_at
                if observed_at is not None
                else time.time()
            ),
        )
        self.repository.save_observation(item)
        self.calculate(slo_id=slo_id)
        return item

    def calculate(
        self,
        *,
        slo_id: str,
        now: int | None = None,
    ) -> ErrorBudgetSnapshot:
        slo = self.repository.get_slo(slo_id)
        if slo is None:
            raise KeyError("SLO bulunamadı")

        current = int(now if now is not None else time.time())
        start = current - slo.window_seconds
        observations = tuple(
            item
            for item in self.repository.list_observations(slo_id)
            if item.observed_at >= start
        )

        total = sum(item.total_events for item in observations)
        good = sum(item.good_events for item in observations)
        bad = total - good

        achieved = good / total if total else 1.0
        allowed_bad = total * (1.0 - slo.target)
        remaining_bad = allowed_bad - bad
        remaining_percent = (
            100.0
            if allowed_bad <= 0
            else max(0.0, remaining_bad / allowed_bad * 100.0)
        )
        burn_rate = (
            0.0
            if allowed_bad <= 0
            else bad / allowed_bad
        )

        if burn_rate >= slo.critical_burn_rate:
            status = "CRITICAL"
        elif burn_rate >= slo.warning_burn_rate:
            status = "WARNING"
        else:
            status = "HEALTHY"

        snapshot = ErrorBudgetSnapshot(
            slo_id=slo.slo_id,
            service=slo.service,
            target=round(slo.target, 6),
            achieved=round(achieved, 6),
            allowed_bad_events=round(allowed_bad, 6),
            consumed_bad_events=bad,
            remaining_bad_events=round(remaining_bad, 6),
            remaining_percent=round(remaining_percent, 6),
            burn_rate=round(burn_rate, 6),
            status=status,
            observed_events=total,
            calculated_at=current,
        )
        return self.repository.save_snapshot(snapshot)

    def reliability_score(
        self,
        *,
        tenant_id: str,
        now: int | None = None,
    ) -> dict:
        snapshots = [
            self.calculate(
                slo_id=slo.slo_id,
                now=now,
            )
            for slo in self.repository.list_slos(tenant_id)
            if slo.enabled
        ]

        if not snapshots:
            return {
                "tenant_id": tenant_id,
                "score": 100,
                "status": "NO_DATA",
                "slo_count": 0,
            }

        scores = [
            max(
                0.0,
                min(
                    100.0,
                    snapshot.remaining_percent,
                ),
            )
            for snapshot in snapshots
        ]
        score = round(sum(scores) / len(scores))
        status = (
            "HEALTHY"
            if score >= 70
            else "AT_RISK"
            if score >= 30
            else "UNHEALTHY"
        )
        return {
            "tenant_id": tenant_id,
            "score": score,
            "status": status,
            "slo_count": len(snapshots),
            "critical_slos": sum(
                1
                for snapshot in snapshots
                if snapshot.status == "CRITICAL"
            ),
            "warning_slos": sum(
                1
                for snapshot in snapshots
                if snapshot.status == "WARNING"
            ),
        }
