from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time


@dataclass(frozen=True)
class AlertPolicy:
    policy_id: str
    tenant_id: str
    trigger: str | None
    minimum_severity: str
    dedup_window_seconds: int
    acknowledge_sla_seconds: int
    escalation_target: str
    enabled: bool
    created_at: int


@dataclass(frozen=True)
class AlertIncident:
    incident_id: str
    alert_id: str
    tenant_id: str
    match_id: str
    trigger: str
    severity: str
    status: str
    owner: str | None
    created_at: int
    acknowledged_at: int | None
    resolved_at: int | None
    escalation_level: int
    escalation_target: str | None


@dataclass(frozen=True)
class SilenceRule:
    silence_id: str
    tenant_id: str
    match_id: str | None
    trigger: str | None
    starts_at: int
    ends_at: int
    reason: str
    created_by: str


class IncidentConflict(RuntimeError):
    pass


class RedisAlertPolicyRepository:
    SEVERITY_ORDER = {
        "LOW": 1,
        "MEDIUM": 2,
        "HIGH": 3,
        "CRITICAL": 4,
    }

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:alert-policy",
        ttl_seconds: int = 7_776_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_policy(
        self,
        policy: AlertPolicy,
    ) -> AlertPolicy:
        self.client.setex(
            self._policy_key(policy.policy_id),
            self.ttl_seconds,
            json.dumps(
                policy.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._policy_index(policy.tenant_id),
            policy.policy_id,
        )
        return policy

    def list_policies(
        self,
        tenant_id: str,
    ) -> tuple[AlertPolicy, ...]:
        items = []
        for policy_id in self.client.smembers(
            self._policy_index(tenant_id)
        ):
            if isinstance(policy_id, bytes):
                policy_id = policy_id.decode("utf-8")
            payload = self.client.get(
                self._policy_key(str(policy_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                AlertPolicy(**json.loads(payload))
            )
        items.sort(
            key=lambda item: item.created_at
        )
        return tuple(items)

    def matching_policy(
        self,
        *,
        tenant_id: str,
        trigger: str,
        severity: str,
    ) -> AlertPolicy | None:
        level = self.SEVERITY_ORDER.get(
            severity,
            0,
        )
        matches = []
        for policy in self.list_policies(tenant_id):
            if not policy.enabled:
                continue
            if (
                policy.trigger is not None
                and policy.trigger != trigger
            ):
                continue
            minimum = self.SEVERITY_ORDER.get(
                policy.minimum_severity,
                0,
            )
            if level < minimum:
                continue
            matches.append(policy)

        if not matches:
            return None

        matches.sort(
            key=lambda item: (
                self.SEVERITY_ORDER.get(
                    item.minimum_severity,
                    0,
                ),
                item.created_at,
            ),
            reverse=True,
        )
        return matches[0]

    def save_silence(
        self,
        silence: SilenceRule,
    ) -> SilenceRule:
        self.client.setex(
            self._silence_key(silence.silence_id),
            max(
                1,
                silence.ends_at - silence.starts_at
                + 3600,
            ),
            json.dumps(
                silence.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._silence_index(silence.tenant_id),
            silence.silence_id,
        )
        return silence

    def is_silenced(
        self,
        *,
        tenant_id: str,
        match_id: str,
        trigger: str,
        now: int,
    ) -> bool:
        for silence_id in self.client.smembers(
            self._silence_index(tenant_id)
        ):
            if isinstance(silence_id, bytes):
                silence_id = silence_id.decode("utf-8")
            payload = self.client.get(
                self._silence_key(str(silence_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            silence = SilenceRule(**json.loads(payload))

            if not (
                silence.starts_at
                <= now
                <= silence.ends_at
            ):
                continue
            if (
                silence.match_id is not None
                and silence.match_id != match_id
            ):
                continue
            if (
                silence.trigger is not None
                and silence.trigger != trigger
            ):
                continue
            return True

        return False

    def reserve_dedup(
        self,
        *,
        tenant_id: str,
        match_id: str,
        trigger: str,
        window_seconds: int,
    ) -> bool:
        key = self._dedup_key(
            tenant_id,
            match_id,
            trigger,
        )
        return bool(
            self.client.set(
                key,
                "1",
                nx=True,
                ex=max(1, window_seconds),
            )
        )

    def save_incident(
        self,
        incident: AlertIncident,
    ) -> AlertIncident:
        self.client.setex(
            self._incident_key(incident.incident_id),
            self.ttl_seconds,
            json.dumps(
                incident.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._incident_index(incident.tenant_id),
            incident.incident_id,
        )
        return incident

    def get_incident(
        self,
        incident_id: str,
    ) -> AlertIncident | None:
        payload = self.client.get(
            self._incident_key(incident_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return AlertIncident(**json.loads(payload))

    def list_incidents(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> tuple[AlertIncident, ...]:
        items = []
        for incident_id in self.client.smembers(
            self._incident_index(tenant_id)
        ):
            if isinstance(incident_id, bytes):
                incident_id = incident_id.decode("utf-8")
            incident = self.get_incident(
                str(incident_id)
            )
            if incident is None:
                continue
            if (
                status is not None
                and incident.status != status
            ):
                continue
            items.append(incident)
        items.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def _policy_key(self, policy_id: str) -> str:
        return f"{self.prefix}:policy:{policy_id}"

    def _policy_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:policies:{tenant_id}"

    def _silence_key(self, silence_id: str) -> str:
        return f"{self.prefix}:silence:{silence_id}"

    def _silence_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:silences:{tenant_id}"

    def _dedup_key(
        self,
        tenant_id: str,
        match_id: str,
        trigger: str,
    ) -> str:
        return (
            f"{self.prefix}:dedup:{tenant_id}:"
            f"{match_id}:{trigger}"
        )

    def _incident_key(self, incident_id: str) -> str:
        return f"{self.prefix}:incident:{incident_id}"

    def _incident_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:incidents:{tenant_id}"


class AlertIncidentService:
    def __init__(
        self,
        *,
        repository,
    ):
        self.repository = repository

    def open_incident(
        self,
        *,
        alert_id: str,
        tenant_id: str,
        match_id: str,
        trigger: str,
        severity: str,
        now: int | None = None,
    ) -> AlertIncident | None:
        current = int(
            now if now is not None
            else time.time()
        )

        policy = self.repository.matching_policy(
            tenant_id=tenant_id,
            trigger=trigger,
            severity=severity,
        )
        if policy is None:
            return None

        if self.repository.is_silenced(
            tenant_id=tenant_id,
            match_id=match_id,
            trigger=trigger,
            now=current,
        ):
            return None

        if not self.repository.reserve_dedup(
            tenant_id=tenant_id,
            match_id=match_id,
            trigger=trigger,
            window_seconds=(
                policy.dedup_window_seconds
            ),
        ):
            return None

        incident_id = hashlib.sha256(
            (
                f"{alert_id}|{tenant_id}|"
                f"{match_id}|{trigger}"
            ).encode("utf-8")
        ).hexdigest()

        incident = AlertIncident(
            incident_id=incident_id,
            alert_id=alert_id,
            tenant_id=tenant_id,
            match_id=match_id,
            trigger=trigger,
            severity=severity,
            status="OPEN",
            owner=None,
            created_at=current,
            acknowledged_at=None,
            resolved_at=None,
            escalation_level=0,
            escalation_target=(
                policy.escalation_target
            ),
        )
        return self.repository.save_incident(
            incident
        )

    def acknowledge(
        self,
        *,
        incident_id: str,
        owner: str,
        now: int | None = None,
    ) -> AlertIncident:
        incident = self._required(incident_id)
        if incident.status == "RESOLVED":
            raise IncidentConflict(
                "Çözülmüş incident acknowledge edilemez"
            )

        current = int(
            now if now is not None
            else time.time()
        )
        updated = AlertIncident(
            **{
                **incident.__dict__,
                "status": "ACKNOWLEDGED",
                "owner": owner,
                "acknowledged_at": current,
            }
        )
        return self.repository.save_incident(
            updated
        )

    def resolve(
        self,
        *,
        incident_id: str,
        owner: str,
        now: int | None = None,
    ) -> AlertIncident:
        incident = self._required(incident_id)
        current = int(
            now if now is not None
            else time.time()
        )
        updated = AlertIncident(
            **{
                **incident.__dict__,
                "status": "RESOLVED",
                "owner": owner,
                "resolved_at": current,
            }
        )
        return self.repository.save_incident(
            updated
        )

    def escalate_due(
        self,
        *,
        tenant_id: str,
        now: int | None = None,
    ) -> tuple[AlertIncident, ...]:
        current = int(
            now if now is not None
            else time.time()
        )
        escalated = []

        for incident in self.repository.list_incidents(
            tenant_id,
            status="OPEN",
            limit=1000,
        ):
            policy = self.repository.matching_policy(
                tenant_id=tenant_id,
                trigger=incident.trigger,
                severity=incident.severity,
            )
            if policy is None:
                continue

            deadline = (
                incident.created_at
                + policy.acknowledge_sla_seconds
            )
            if current < deadline:
                continue

            updated = AlertIncident(
                **{
                    **incident.__dict__,
                    "status": "ESCALATED",
                    "escalation_level": (
                        incident.escalation_level + 1
                    ),
                    "escalation_target": (
                        policy.escalation_target
                    ),
                }
            )
            self.repository.save_incident(updated)
            escalated.append(updated)

        return tuple(escalated)

    def _required(
        self,
        incident_id: str,
    ) -> AlertIncident:
        incident = self.repository.get_incident(
            incident_id
        )
        if incident is None:
            raise KeyError(
                "Alert incident bulunamadı"
            )
        return incident
