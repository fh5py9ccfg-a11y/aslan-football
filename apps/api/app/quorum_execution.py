from __future__ import annotations
from dataclasses import dataclass
import json
import secrets
import time

@dataclass(frozen=True)
class QuorumExecutionRecord:
    request_id: str
    claim_id: str
    status: str
    owner: str
    owner_token: str
    started_at: int
    heartbeat_at: int
    lease_expires_at: int
    attempts: int
    completed_at: int | None
    result_status: str | None
    reason: str | None

class ExecutionInProgress(RuntimeError):
    pass

class ExecutionOwnershipLost(RuntimeError):
    pass

class RedisQuorumExecutionRepository:
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
    if existing.status ~= "IN_PROGRESS" then
        return {2, raw}
    end

    if existing.owner_token ~= owner_token then
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

    if existing.status == "COMPLETED" then
        return {3, raw}
    end

    redis.call("SET", key, payload, "EX", ttl)
    return {1, payload}
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:maintenance:quorum-execution",
        ttl_seconds: int = 2_592_000,
        lease_seconds: int = 60,
    ):
        if ttl_seconds <= 0 or lease_seconds <= 0:
            raise ValueError("Execution süreleri pozitif olmalıdır")
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds
        self.lease_seconds = lease_seconds

    def claim(
        self,
        *,
        request_id: str,
        claim_id: str,
        owner: str,
        now: int | None = None,
    ) -> tuple[bool, QuorumExecutionRecord]:
        current = int(now if now is not None else time.time())
        existing = self.get(request_id)
        attempts = (
            existing.attempts + 1
            if existing is not None
            else 1
        )
        owner_token = secrets.token_urlsafe(18)
        record = QuorumExecutionRecord(
            request_id=request_id,
            claim_id=claim_id,
            status="IN_PROGRESS",
            owner=owner,
            owner_token=owner_token,
            started_at=current,
            heartbeat_at=current,
            lease_expires_at=current + self.lease_seconds,
            attempts=attempts,
            completed_at=None,
            result_status=None,
            reason=None,
        )
        result = self.client.eval(
            self.CLAIM_SCRIPT,
            1,
            self._key(request_id),
            current,
            self._serialize(record),
            self.ttl_seconds,
        )
        created = int(result[0]) == 1
        return created, self._deserialize(result[1])

    def heartbeat(
        self,
        record: QuorumExecutionRecord,
        *,
        now: int | None = None,
    ) -> QuorumExecutionRecord:
        current = int(now if now is not None else time.time())
        result = self.client.eval(
            self.HEARTBEAT_SCRIPT,
            1,
            self._key(record.request_id),
            record.owner_token,
            current,
            current + self.lease_seconds,
            self.ttl_seconds,
        )
        code = int(result[0])
        if code == 0:
            raise KeyError("Execution kaydı bulunamadı")
        if code in {2, 3}:
            raise ExecutionOwnershipLost(
                "Execution ownership kaybedildi"
            )
        return self._deserialize(result[1])

    def complete(
        self,
        *,
        record: QuorumExecutionRecord,
        result_status: str,
        reason: str,
        now: int | None = None,
    ) -> QuorumExecutionRecord:
        current = int(now if now is not None else time.time())
        completed = QuorumExecutionRecord(
            request_id=record.request_id,
            claim_id=record.claim_id,
            status="COMPLETED",
            owner=record.owner,
            owner_token=record.owner_token,
            started_at=record.started_at,
            heartbeat_at=record.heartbeat_at,
            lease_expires_at=record.lease_expires_at,
            attempts=record.attempts,
            completed_at=current,
            result_status=result_status,
            reason=reason,
        )
        result = self.client.eval(
            self.COMPLETE_SCRIPT,
            1,
            self._key(record.request_id),
            record.owner_token,
            self._serialize(completed),
            self.ttl_seconds,
        )
        code = int(result[0])
        if code == 0:
            raise KeyError("Execution kaydı bulunamadı")
        if code == 2:
            raise ExecutionOwnershipLost(
                "Stale execution owner complete işlemi yapamaz"
            )
        if code == 3:
            return self._deserialize(result[1])
        return completed

    def get(
        self,
        request_id: str,
    ) -> QuorumExecutionRecord | None:
        payload = self.client.get(self._key(request_id))
        if payload is None:
            return None
        return self._deserialize(payload)

    def _key(self, request_id: str) -> str:
        return f"{self.prefix}:{request_id}"

    @staticmethod
    def _serialize(record: QuorumExecutionRecord) -> str:
        return json.dumps(
            record.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize(payload) -> QuorumExecutionRecord:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        return QuorumExecutionRecord(
            request_id=str(data["request_id"]),
            claim_id=str(data["claim_id"]),
            status=str(data["status"]),
            owner=str(data["owner"]),
            owner_token=str(
                data.get("owner_token") or "legacy-owner-token"
            ),
            started_at=int(data["started_at"]),
            heartbeat_at=int(
                data.get("heartbeat_at", data["started_at"])
            ),
            lease_expires_at=int(
                data.get(
                    "lease_expires_at",
                    data["started_at"],
                )
            ),
            attempts=int(data.get("attempts", 1)),
            completed_at=(
                int(data["completed_at"])
                if data.get("completed_at") is not None
                else None
            ),
            result_status=(
                str(data["result_status"])
                if data.get("result_status") is not None
                else None
            ),
            reason=(
                str(data["reason"])
                if data.get("reason") is not None
                else None
            ),
        )
