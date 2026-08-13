from __future__ import annotations
from dataclasses import dataclass
import asyncio
import json
import logging
import secrets
import time

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class OutboxDeliveryRecord:
    event_id: str
    status: str
    owner: str
    owner_token: str
    attempts: int
    claimed_at: int
    heartbeat_at: int
    lease_expires_at: int
    next_attempt_at: int | None
    delivered_at: int | None
    error: str | None

class OutboxOwnershipLost(RuntimeError):
    pass

class RedisOutboxDeliveryRepository:
    CLAIM_SCRIPT = '''
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local payload = ARGV[2]
    local ttl = tonumber(ARGV[3])

    local raw = redis.call("GET", key)
    if raw then
        local existing = cjson.decode(raw)

        if existing.status == "DELIVERED" then
            return {0, raw}
        end

        local next_attempt_at = tonumber(
            existing.next_attempt_at or 0
        )
        if next_attempt_at > now then
            return {0, raw}
        end

        local lease_expires_at = tonumber(
            existing.lease_expires_at or 0
        )
        if existing.status == "IN_PROGRESS"
            and lease_expires_at > now then
            return {0, raw}
        end
    end

    redis.call("SET", key, payload, "EX", ttl)
    return {1, payload}
    '''

    HEARTBEAT_SCRIPT = '''
    local key = KEYS[1]
    local owner_token = ARGV[1]
    local now = tonumber(ARGV[2])
    local lease_expires_at = tonumber(ARGV[3])
    local ttl = tonumber(ARGV[4])

    local raw = redis.call("GET", key)
    if not raw then return {0, "missing"} end
    local existing = cjson.decode(raw)
    if existing.owner_token ~= owner_token then return {2, raw} end
    if existing.status ~= "IN_PROGRESS" then return {3, raw} end
    existing.heartbeat_at = now
    existing.lease_expires_at = lease_expires_at
    local payload = cjson.encode(existing)
    redis.call("SET", key, payload, "EX", ttl)
    return {1, payload}
    '''

    UPDATE_SCRIPT = '''
    local key = KEYS[1]
    local owner_token = ARGV[1]
    local payload = ARGV[2]
    local ttl = tonumber(ARGV[3])

    local raw = redis.call("GET", key)
    if not raw then
        return {0, "missing"}
    end

    local existing = cjson.decode(raw)
    if existing.owner_token ~= owner_token then
        return {2, raw}
    end

    redis.call("SET", key, payload, "EX", ttl)
    return {1, payload}
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:compensation-outbox-delivery",
        lease_seconds: int = 60,
        ttl_seconds: int = 2_592_000,
    ):
        if lease_seconds <= 0 or ttl_seconds <= 0:
            raise ValueError("Outbox delivery süreleri pozitif olmalıdır")
        self.client = client
        self.prefix = prefix
        self.lease_seconds = lease_seconds
        self.ttl_seconds = ttl_seconds

    def claim(
        self,
        *,
        event_id: str,
        owner: str,
        now: int | None = None,
    ) -> tuple[bool, OutboxDeliveryRecord]:
        current = int(now if now is not None else time.time())
        existing = self.get(event_id)
        attempts = existing.attempts + 1 if existing is not None else 1

        record = OutboxDeliveryRecord(
            event_id=event_id,
            status="IN_PROGRESS",
            owner=owner,
            owner_token=secrets.token_urlsafe(18),
            attempts=attempts,
            claimed_at=current,
            heartbeat_at=current,
            lease_expires_at=current + self.lease_seconds,
            next_attempt_at=None,
            delivered_at=None,
            error=None,
        )
        result = self.client.eval(
            self.CLAIM_SCRIPT,
            1,
            self._key(event_id),
            current,
            self._serialize(record),
            self.ttl_seconds,
        )
        return int(result[0]) == 1, self._deserialize(result[1])


    def heartbeat(
        self,
        record: OutboxDeliveryRecord,
        *,
        now: int | None = None,
    ) -> OutboxDeliveryRecord:
        current = int(now if now is not None else time.time())
        result = self.client.eval(
            self.HEARTBEAT_SCRIPT,
            1,
            self._key(record.event_id),
            record.owner_token,
            current,
            current + self.lease_seconds,
            self.ttl_seconds,
        )
        code = int(result[0])
        if code == 0:
            raise KeyError("Outbox delivery kaydı bulunamadı")
        if code in {2, 3}:
            raise OutboxOwnershipLost("Outbox delivery ownership kaybedildi")
        return self._deserialize(result[1])

    def mark_delivered(
        self,
        record: OutboxDeliveryRecord,
        *,
        now: int | None = None,
    ) -> OutboxDeliveryRecord:
        current = int(now if now is not None else time.time())
        delivered = OutboxDeliveryRecord(
            **{
                **record.__dict__,
                "status": "DELIVERED",
                "heartbeat_at": current,
                "delivered_at": current,
                "lease_expires_at": current,
                "next_attempt_at": None,
                "error": None,
            }
        )
        return self._update(record, delivered)

    def schedule_retry(
        self,
        record: OutboxDeliveryRecord,
        *,
        error: str,
        next_attempt_at: int,
    ) -> OutboxDeliveryRecord:
        retry = OutboxDeliveryRecord(
            **{
                **record.__dict__,
                "status": "RETRY_SCHEDULED",
                "lease_expires_at": 0,
                "next_attempt_at": next_attempt_at,
                "error": error[:1000],
            }
        )
        return self._update(record, retry)

    def mark_dead_letter(
        self,
        record: OutboxDeliveryRecord,
        *,
        error: str,
    ) -> OutboxDeliveryRecord:
        dead = OutboxDeliveryRecord(
            **{
                **record.__dict__,
                "status": "DEAD_LETTER",
                "lease_expires_at": 0,
                "next_attempt_at": None,
                "error": error[:1000],
            }
        )
        return self._update(record, dead)

    def get(self, event_id: str) -> OutboxDeliveryRecord | None:
        payload = self.client.get(self._key(event_id))
        if payload is None:
            return None
        return self._deserialize(payload)

    def _update(
        self,
        current: OutboxDeliveryRecord,
        updated: OutboxDeliveryRecord,
    ) -> OutboxDeliveryRecord:
        result = self.client.eval(
            self.UPDATE_SCRIPT,
            1,
            self._key(current.event_id),
            current.owner_token,
            self._serialize(updated),
            self.ttl_seconds,
        )
        code = int(result[0])
        if code == 0:
            raise KeyError("Outbox delivery kaydı bulunamadı")
        if code == 2:
            raise OutboxOwnershipLost(
                "Stale publisher outbox durumunu güncelleyemez"
            )
        return updated

    def _key(self, event_id: str) -> str:
        return f"{self.prefix}:{event_id}"

    @staticmethod
    def _serialize(record: OutboxDeliveryRecord) -> str:
        return json.dumps(
            record.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize(payload) -> OutboxDeliveryRecord:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data.setdefault("heartbeat_at", data["claimed_at"])
        return OutboxDeliveryRecord(**data)

class CompensationOutboxPublisher:
    def __init__(
        self,
        *,
        committer,
        delivery_repository,
        transport,
        max_attempts: int = 5,
        base_backoff_seconds: int = 30,
        receipt_repository=None,
        heartbeat_interval_seconds: float = 15.0,
        ordering_repository=None,
    ):
        if max_attempts <= 0 or base_backoff_seconds <= 0:
            raise ValueError("Publisher ayarları pozitif olmalıdır")
        self.committer = committer
        self.delivery_repository = delivery_repository
        self.transport = transport
        self.max_attempts = max_attempts
        self.base_backoff_seconds = base_backoff_seconds
        self.receipt_repository = receipt_repository
        self.ordering_repository = ordering_repository
        from .outbox_delivery_heartbeat import OutboxPublishGuard
        self.publish_guard = OutboxPublishGuard(
            repository=delivery_repository,
            heartbeat_interval_seconds=heartbeat_interval_seconds,
        )


    def publish_event(
        self,
        event,
        *,
        now: int | None = None,
    ) -> OutboxDeliveryRecord:
        return asyncio.run(self.publish_event_async(event, now=now))

    async def publish_event_async(
        self,
        event,
        *,
        now: int | None = None,
    ) -> OutboxDeliveryRecord:
        current = int(now if now is not None else time.time())
        created, delivery = self.delivery_repository.claim(
            event_id=event.event_id,
            owner=secrets.token_urlsafe(12),
            now=current,
        )
        if not created:
            return delivery

        guarded = await self.publish_guard.run(
            record=delivery,
            operation=lambda: self.transport.publish(
                event_id=event.event_id,
                payload=event.__dict__,
            ),
        )
        if guarded.ownership_lost:
            return OutboxDeliveryRecord(**{
                **delivery.__dict__,
                "status": "OWNERSHIP_LOST",
                "error": guarded.error,
            })

        error = guarded.error
        if error is None:
            receipt = guarded.receipt
            if receipt is None:
                from .outbox_transport import PublishReceipt
                receipt = PublishReceipt(
                    event_id=event.event_id,
                    transport=getattr(self.transport, "name", "legacy"),
                    destination="legacy-transport",
                    accepted=True,
                    external_id=event.event_id,
                    payload_sha256="",
                    published_at=current,
                )
            if not receipt.accepted:
                error = "Transport olayı kabul etmedi"
            elif receipt.event_id != event.event_id:
                error = "Transport receipt event kimliği uyuşmuyor"
            else:
                if self.ordering_repository is not None:
                    self.ordering_repository.advance(
                        partition=event.partition,
                        sequence=event.sequence,
                        event_id=event.event_id,
                    )
                if self.receipt_repository is not None:
                    self.receipt_repository.save(receipt)
                try:
                    return self.delivery_repository.mark_delivered(delivery, now=current)
                except OutboxOwnershipLost:
                    return OutboxDeliveryRecord(**{
                        **delivery.__dict__,
                        "status": "OWNERSHIP_LOST",
                        "error": "Stale publisher ACK yazamadı",
                    })

        try:
            if delivery.attempts >= self.max_attempts:
                return self.delivery_repository.mark_dead_letter(delivery, error=error)
            delay = self.base_backoff_seconds * (2 ** (delivery.attempts - 1))
            return self.delivery_repository.schedule_retry(
                delivery,
                error=error,
                next_attempt_at=current + delay,
            )
        except OutboxOwnershipLost:
            return OutboxDeliveryRecord(**{
                **delivery.__dict__,
                "status": "OWNERSHIP_LOST",
                "error": "Stale publisher durum yazamadı",
            })
    def publish_batch(
        self,
        *,
        limit: int = 100,
        now: int | None = None,
    ) -> tuple[OutboxDeliveryRecord, ...]:
        return asyncio.run(self.publish_batch_async(limit=limit, now=now))

    async def publish_batch_async(
        self,
        *,
        limit: int = 100,
        now: int | None = None,
    ) -> tuple[OutboxDeliveryRecord, ...]:
        events = self.committer.list_events(limit=limit)
        results = []
        for event in events:
            results.append(await self.publish_event_async(event, now=now))
        return tuple(results)

class OutboxPublisherWorker:
    def __init__(
        self,
        *,
        publisher: CompensationOutboxPublisher,
        interval_seconds: float = 10.0,
        batch_size: int = 100,
    ):
        self.publisher = publisher
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()
        self.last_results = ()

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(
                self._run(),
                name="compensation-outbox-publisher",
            )

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def run_once(self):
        publish_async = getattr(self.publisher, "publish_batch_async", None)
        if callable(publish_async):
            self.last_results = await publish_async(limit=self.batch_size)
        else:
            self.last_results = await asyncio.to_thread(
                self.publisher.publish_batch,
                limit=self.batch_size,
            )
        return self.last_results

    async def _run(self):
        while not self._stopping.is_set():
            try:
                await self.run_once()
            except Exception as exc:
                logger.warning(
                    "Outbox publish cycle failed: %s",
                    exc,
                )

            try:
                await asyncio.wait_for(
                    self._stopping.wait(),
                    timeout=self.interval_seconds,
                )
            except asyncio.TimeoutError:
                pass
