from __future__ import annotations
from dataclasses import dataclass
import asyncio, hashlib, json, time

@dataclass(frozen=True)
class AlertSubscription:
    subscription_id: str
    tenant_id: str
    match_id: str | None
    trigger: str | None
    minimum_severity: str
    destination: str
    enabled: bool
    created_at: int

@dataclass(frozen=True)
class AlertMessage:
    alert_id: str
    tenant_id: str
    match_id: str
    trigger: str
    severity: str
    title: str
    body: str
    payload: dict
    created_at: int

@dataclass(frozen=True)
class DeliveryAttempt:
    delivery_id: str
    alert_id: str
    subscription_id: str
    destination: str
    attempt: int
    status: str
    response_code: int | None
    error: str | None
    created_at: int

class RedisAlertRepository:
    SEVERITY_ORDER = {"LOW":1, "MEDIUM":2, "HIGH":3, "CRITICAL":4}

    def __init__(self, client, *, prefix="aslan:alerting", ttl_seconds=2592000):
        self.client, self.prefix, self.ttl_seconds = client, prefix, ttl_seconds

    def save_subscription(self, item):
        self.client.setex(
            f"{self.prefix}:subscription:{item.subscription_id}",
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False, separators=(",", ":")),
        )
        self.client.sadd(f"{self.prefix}:subscriptions:{item.tenant_id}", item.subscription_id)
        return item

    def list_subscriptions(self, tenant_id):
        items = []
        for sid in self.client.smembers(f"{self.prefix}:subscriptions:{tenant_id}"):
            if isinstance(sid, bytes): sid = sid.decode()
            payload = self.client.get(f"{self.prefix}:subscription:{sid}")
            if payload is None: continue
            if isinstance(payload, bytes): payload = payload.decode()
            items.append(AlertSubscription(**json.loads(payload)))
        return tuple(sorted(items, key=lambda x: x.created_at))

    def matching_subscriptions(self, alert):
        level = self.SEVERITY_ORDER.get(alert.severity, 0)
        result = []
        for item in self.list_subscriptions(alert.tenant_id):
            if not item.enabled: continue
            if item.match_id is not None and item.match_id != alert.match_id: continue
            if item.trigger is not None and item.trigger != alert.trigger: continue
            if level < self.SEVERITY_ORDER.get(item.minimum_severity, 0): continue
            result.append(item)
        return tuple(result)

    def save_attempt(self, item):
        self.client.setex(
            f"{self.prefix}:attempt:{item.delivery_id}",
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False, separators=(",", ":")),
        )
        self.client.sadd(f"{self.prefix}:attempts:{item.alert_id}", item.delivery_id)
        return item

    def list_attempts(self, alert_id):
        items = []
        for did in self.client.smembers(f"{self.prefix}:attempts:{alert_id}"):
            if isinstance(did, bytes): did = did.decode()
            payload = self.client.get(f"{self.prefix}:attempt:{did}")
            if payload is None: continue
            if isinstance(payload, bytes): payload = payload.decode()
            items.append(DeliveryAttempt(**json.loads(payload)))
        items.sort(key=lambda x: x.attempt)
        return tuple(items)

    def add_dead_letter(self, *, alert, subscription, error):
        self.client.rpush(
            f"{self.prefix}:dead-letter",
            json.dumps(
                {"alert":alert.__dict__, "subscription":subscription.__dict__, "error":error},
                ensure_ascii=False, separators=(",", ":"),
            ),
        )

    def list_dead_letters(self, *, limit=100):
        values = self.client.lrange(f"{self.prefix}:dead-letter", 0, max(0, limit-1))
        out = []
        for payload in values:
            if isinstance(payload, bytes): payload = payload.decode()
            out.append(json.loads(payload))
        return tuple(out)

class WebhookDeliveryClient:
    def __init__(self, sender): self.sender = sender
    async def send(self, *, destination, payload):
        result = self.sender(destination, payload)
        if asyncio.iscoroutine(result): result = await result
        return int(result)

class AlertDeliveryService:
    def __init__(self, *, repository, client, max_attempts=3, backoff_seconds=0.01):
        self.repository = repository
        self.client = client
        self.max_attempts = max_attempts
        self.backoff_seconds = backoff_seconds

    async def publish(self, alert):
        subscriptions = self.repository.matching_subscriptions(alert)
        delivered = failed = 0
        for subscription in subscriptions:
            if await self._deliver(alert, subscription): delivered += 1
            else: failed += 1
        return {"alert_id":alert.alert_id, "matched":len(subscriptions), "delivered":delivered, "failed":failed}

    async def _deliver(self, alert, subscription):
        last_error = None
        for attempt in range(1, self.max_attempts+1):
            did = hashlib.sha256(
                f"{alert.alert_id}|{subscription.subscription_id}|{attempt}".encode()
            ).hexdigest()
            try:
                code = await self.client.send(
                    destination=subscription.destination,
                    payload={
                        "id":alert.alert_id, "title":alert.title, "body":alert.body,
                        "severity":alert.severity, "payload":alert.payload,
                    },
                )
                ok = 200 <= code < 300
                self.repository.save_attempt(DeliveryAttempt(
                    did, alert.alert_id, subscription.subscription_id,
                    subscription.destination, attempt,
                    "DELIVERED" if ok else "FAILED", code, None, int(time.time())
                ))
                if ok: return True
                last_error = f"HTTP {code}"
            except Exception as exc:
                last_error = str(exc)
                self.repository.save_attempt(DeliveryAttempt(
                    did, alert.alert_id, subscription.subscription_id,
                    subscription.destination, attempt, "FAILED", None,
                    last_error, int(time.time())
                ))
            if attempt < self.max_attempts:
                await asyncio.sleep(self.backoff_seconds * attempt)
        self.repository.add_dead_letter(
            alert=alert, subscription=subscription, error=last_error or "unknown"
        )
        return False
