from __future__ import annotations
from dataclasses import dataclass
import json
import secrets
import time

@dataclass(frozen=True)
class CompensationExecutionLease:
    compensation_id: str
    owner: str
    owner_token: str
    status: str
    claimed_at: int
    heartbeat_at: int
    lease_expires_at: int
    attempts: int

class CompensationOwnershipLost(RuntimeError):
    pass

class RedisCompensationExecutionRepository:
    CLAIM_SCRIPT = '''
    local key = KEYS[1]
    local now = tonumber(ARGV[1])
    local payload = ARGV[2]
    local ttl = tonumber(ARGV[3])

    local existing_raw = redis.call("GET", key)
    if existing_raw then
        local existing = cjson.decode(existing_raw)
        if existing.status == "COMPLETED" then
            return {0, existing_raw}
        end
        if tonumber(existing.lease_expires_at or 0) > now then
            return {0, existing_raw}
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
    if not raw then
        return {0, "missing"}
    end

    local existing = cjson.decode(raw)
    if existing.owner_token ~= owner_token then
        return {2, raw}
    end
    if existing.status ~= "IN_PROGRESS" then
        return {3, raw}
    end

    existing.heartbeat_at = now
    existing.lease_expires_at = lease_expires_at
    local payload = cjson.encode(existing)
    redis.call("SET", key, payload, "EX", ttl)
    return {1, payload}
    '''

    COMPLETE_SCRIPT = '''
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
        prefix: str = "aslan:compensation-execution",
        lease_seconds: int = 60,
        ttl_seconds: int = 2_592_000,
    ):
        if lease_seconds <= 0 or ttl_seconds <= 0:
            raise ValueError("Execution süreleri pozitif olmalıdır")
        self.client = client
        self.prefix = prefix
        self.lease_seconds = lease_seconds
        self.ttl_seconds = ttl_seconds

    def claim(
        self,
        *,
        compensation_id: str,
        owner: str,
        now: int | None = None,
    ) -> tuple[bool, CompensationExecutionLease]:
        current = int(now if now is not None else time.time())
        existing = self.get(compensation_id)
        attempts = existing.attempts + 1 if existing is not None else 1

        record = CompensationExecutionLease(
            compensation_id=compensation_id,
            owner=owner,
            owner_token=secrets.token_urlsafe(18),
            status="IN_PROGRESS",
            claimed_at=current,
            heartbeat_at=current,
            lease_expires_at=current + self.lease_seconds,
            attempts=attempts,
        )
        result = self.client.eval(
            self.CLAIM_SCRIPT,
            1,
            self._key(compensation_id),
            current,
            self._serialize(record),
            self.ttl_seconds,
        )
        return int(result[0]) == 1, self._deserialize(result[1])

    def heartbeat(
        self,
        record: CompensationExecutionLease,
        *,
        now: int | None = None,
    ) -> CompensationExecutionLease:
        current = int(now if now is not None else time.time())
        result = self.client.eval(
            self.HEARTBEAT_SCRIPT,
            1,
            self._key(record.compensation_id),
            record.owner_token,
            current,
            current + self.lease_seconds,
            self.ttl_seconds,
        )
        code = int(result[0])
        if code == 0:
            raise KeyError("Compensation execution kaydı bulunamadı")
        if code in {2, 3}:
            raise CompensationOwnershipLost(
                "Compensation execution ownership kaybedildi"
            )
        return self._deserialize(result[1])

    def complete(
        self,
        record: CompensationExecutionLease,
    ) -> CompensationExecutionLease:
        completed = CompensationExecutionLease(
            **{
                **record.__dict__,
                "status": "COMPLETED",
            }
        )
        result = self.client.eval(
            self.COMPLETE_SCRIPT,
            1,
            self._key(record.compensation_id),
            record.owner_token,
            self._serialize(completed),
            self.ttl_seconds,
        )
        code = int(result[0])
        if code == 0:
            raise KeyError("Compensation execution kaydı bulunamadı")
        if code == 2:
            raise CompensationOwnershipLost(
                "Stale compensation worker complete yapamaz"
            )
        return completed

    def get(
        self,
        compensation_id: str,
    ) -> CompensationExecutionLease | None:
        payload = self.client.get(self._key(compensation_id))
        if payload is None:
            return None
        return self._deserialize(payload)

    def _key(self, compensation_id: str) -> str:
        return f"{self.prefix}:{compensation_id}"

    @staticmethod
    def _serialize(record: CompensationExecutionLease) -> str:
        return json.dumps(
            record.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize(payload) -> CompensationExecutionLease:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        return CompensationExecutionLease(
            compensation_id=str(data["compensation_id"]),
            owner=str(data["owner"]),
            owner_token=str(data["owner_token"]),
            status=str(data["status"]),
            claimed_at=int(data["claimed_at"]),
            heartbeat_at=int(data["heartbeat_at"]),
            lease_expires_at=int(data["lease_expires_at"]),
            attempts=int(data.get("attempts", 1)),
        )
