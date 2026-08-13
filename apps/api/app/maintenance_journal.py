from __future__ import annotations
from dataclasses import dataclass
import json
import secrets
import time

from .distributed_lease import StaleFencingToken

@dataclass(frozen=True)
class MaintenanceClaim:
    claim_id: str
    owner_id: str
    index_key: str
    phase: str
    fencing_token: int
    claimed_at: int
    heartbeat_at: int
    expires_at: int
    attempts: int
    status: str

@dataclass(frozen=True)
class QuarantinedIndex:
    claim_id: str
    index_key: str
    phase: str
    attempts: int
    error: str
    quarantined_at: int
    fencing_token: int

class RedisMaintenanceJournal:
    CLAIM_SCRIPT = '''
    local claim_key = KEYS[1]
    local fence_key = KEYS[2]
    local token = tonumber(ARGV[1])
    local payload = ARGV[2]
    local ttl = tonumber(ARGV[3])
    local now = tonumber(ARGV[4])

    local current_fence = tonumber(redis.call("GET", fence_key) or "0")
    if token < current_fence then
        return {-1, current_fence}
    end

    local existing = redis.call("GET", claim_key)
    if existing then
        local current = cjson.decode(existing)
        if tonumber(current.expires_at or 0) > now then
            return {0, existing}
        end
    end

    redis.call("SET", fence_key, token)
    redis.call("SET", claim_key, payload, "EX", ttl)
    return {1, payload}
    '''

    HEARTBEAT_SCRIPT = '''
    local claim_key = KEYS[1]
    local fence_key = KEYS[2]
    local token = tonumber(ARGV[1])
    local owner_id = ARGV[2]
    local now = tonumber(ARGV[3])
    local expires_at = tonumber(ARGV[4])
    local ttl = tonumber(ARGV[5])

    local current_fence = tonumber(redis.call("GET", fence_key) or "0")
    if token < current_fence then
        return {-1, current_fence}
    end

    local raw = redis.call("GET", claim_key)
    if not raw then
        return {0, "missing"}
    end

    local data = cjson.decode(raw)
    if data.owner_id ~= owner_id then
        return {0, "owner"}
    end

    data.heartbeat_at = now
    data.expires_at = expires_at
    redis.call("SET", fence_key, token)
    redis.call("SET", claim_key, cjson.encode(data), "EX", ttl)
    return {1, cjson.encode(data)}
    '''

    COMPLETE_SCRIPT = '''
    local claim_key = KEYS[1]
    local done_key = KEYS[2]
    local fence_key = KEYS[3]
    local token = tonumber(ARGV[1])
    local owner_id = ARGV[2]
    local completed_payload = ARGV[3]
    local done_ttl = tonumber(ARGV[4])

    local current_fence = tonumber(redis.call("GET", fence_key) or "0")
    if token < current_fence then
        return {-1, current_fence}
    end

    local raw = redis.call("GET", claim_key)
    if raw then
        local data = cjson.decode(raw)
        if data.owner_id ~= owner_id then
            return {0, "owner"}
        end
    end

    redis.call("SET", fence_key, token)
    redis.call("SET", done_key, completed_payload, "EX", done_ttl)
    redis.call("DEL", claim_key)
    return {1, token}
    '''

    QUARANTINE_SCRIPT = '''
    local claim_key = KEYS[1]
    local quarantine_key = KEYS[2]
    local fence_key = KEYS[3]
    local token = tonumber(ARGV[1])
    local owner_id = ARGV[2]
    local payload = ARGV[3]
    local ttl = tonumber(ARGV[4])

    local current_fence = tonumber(redis.call("GET", fence_key) or "0")
    if token < current_fence then
        return {-1, current_fence}
    end

    local raw = redis.call("GET", claim_key)
    if raw then
        local data = cjson.decode(raw)
        if data.owner_id ~= owner_id then
            return {0, "owner"}
        end
    end

    redis.call("SET", fence_key, token)
    redis.call("SET", quarantine_key, payload, "EX", ttl)
    redis.call("DEL", claim_key)
    return {1, token}
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:maintenance:journal",
        fence_key: str = "aslan:maintenance:session-index:fence",
        claim_ttl_seconds: int = 120,
        completed_ttl_seconds: int = 86400,
        quarantine_ttl_seconds: int = 604800,
        max_attempts: int = 3,
    ):
        if min(
            claim_ttl_seconds,
            completed_ttl_seconds,
            quarantine_ttl_seconds,
            max_attempts,
        ) <= 0:
            raise ValueError("Journal değerleri pozitif olmalıdır")
        self.client = client
        self.prefix = prefix
        self.fence_key = fence_key
        self.claim_ttl_seconds = claim_ttl_seconds
        self.completed_ttl_seconds = completed_ttl_seconds
        self.quarantine_ttl_seconds = quarantine_ttl_seconds
        self.max_attempts = max_attempts

    def claim(
        self,
        *,
        claim_id: str,
        index_key: str,
        phase: str,
        fencing_token: int,
        owner_id: str | None = None,
        now: int | None = None,
    ) -> MaintenanceClaim | None:
        current = int(now if now is not None else time.time())
        existing = self.get_claim(claim_id)
        attempts = (
            existing.attempts + 1
            if existing is not None
            else 1
        )
        claim = MaintenanceClaim(
            claim_id=claim_id,
            owner_id=owner_id or secrets.token_urlsafe(12),
            index_key=index_key,
            phase=phase,
            fencing_token=fencing_token,
            claimed_at=current,
            heartbeat_at=current,
            expires_at=current + self.claim_ttl_seconds,
            attempts=attempts,
            status="CLAIMED",
        )
        result = self.client.eval(
            self.CLAIM_SCRIPT,
            2,
            self._claim_key(claim_id),
            self.fence_key,
            fencing_token,
            self._serialize(claim),
            self.claim_ttl_seconds,
            current,
        )
        code = int(result[0])
        if code == -1:
            raise StaleFencingToken(
                "Bakım journal fencing token eski; claim reddedildi"
            )
        if code == 0:
            return None
        return claim

    def heartbeat(
        self,
        claim: MaintenanceClaim,
        *,
        now: int | None = None,
    ) -> MaintenanceClaim:
        current = int(now if now is not None else time.time())
        result = self.client.eval(
            self.HEARTBEAT_SCRIPT,
            2,
            self._claim_key(claim.claim_id),
            self.fence_key,
            claim.fencing_token,
            claim.owner_id,
            current,
            current + self.claim_ttl_seconds,
            self.claim_ttl_seconds,
        )
        code = int(result[0])
        if code == -1:
            raise StaleFencingToken(
                "Bakım journal heartbeat fencing token eski"
            )
        if code == 0:
            raise RuntimeError("Bakım claim sahipliği kaybedildi")
        return self._deserialize_claim(result[1])

    def complete(
        self,
        *,
        claim: MaintenanceClaim,
        removed: int,
        repaired: int,
        completed_at: int | None = None,
    ) -> None:
        current = int(
            completed_at if completed_at is not None else time.time()
        )
        payload = json.dumps(
            {
                **claim.__dict__,
                "status": "COMPLETED",
                "completed_at": current,
                "orphan_members_removed": removed,
                "ttl_repairs": repaired,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result = self.client.eval(
            self.COMPLETE_SCRIPT,
            3,
            self._claim_key(claim.claim_id),
            self._done_key(claim.claim_id),
            self.fence_key,
            claim.fencing_token,
            claim.owner_id,
            payload,
            self.completed_ttl_seconds,
        )
        self._assert_result(result, "complete")

    def quarantine(
        self,
        *,
        claim: MaintenanceClaim,
        error: str,
        quarantined_at: int | None = None,
    ) -> QuarantinedIndex:
        current = int(
            quarantined_at if quarantined_at is not None else time.time()
        )
        item = QuarantinedIndex(
            claim_id=claim.claim_id,
            index_key=claim.index_key,
            phase=claim.phase,
            attempts=claim.attempts,
            error=error[:1000],
            quarantined_at=current,
            fencing_token=claim.fencing_token,
        )
        payload = json.dumps(
            item.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result = self.client.eval(
            self.QUARANTINE_SCRIPT,
            3,
            self._claim_key(claim.claim_id),
            self._quarantine_key(claim.claim_id),
            self.fence_key,
            claim.fencing_token,
            claim.owner_id,
            payload,
            self.quarantine_ttl_seconds,
        )
        self._assert_result(result, "quarantine")
        return item

    def should_quarantine(
        self,
        claim: MaintenanceClaim,
    ) -> bool:
        return claim.attempts >= self.max_attempts

    def is_completed(self, claim_id: str) -> bool:
        return bool(self.client.exists(self._done_key(claim_id)))

    def is_quarantined(self, claim_id: str) -> bool:
        return bool(
            self.client.exists(
                self._quarantine_key(claim_id)
            )
        )

    def get_claim(
        self,
        claim_id: str,
    ) -> MaintenanceClaim | None:
        payload = self.client.get(self._claim_key(claim_id))
        return (
            self._deserialize_claim(payload)
            if payload is not None
            else None
        )

    def recoverable_claims(self) -> tuple[MaintenanceClaim, ...]:
        return tuple(
            self._scan_items(
                pattern=f"{self.prefix}:claim:*",
                parser=self._deserialize_claim,
            )
        )

    def quarantined_indexes(self) -> tuple[QuarantinedIndex, ...]:
        return tuple(
            self._scan_items(
                pattern=f"{self.prefix}:quarantine:*",
                parser=self._deserialize_quarantine,
            )
        )

    def _scan_items(self, *, pattern, parser):
        items = []
        cursor = 0
        while True:
            cursor, keys = self.client.scan(
                cursor=cursor,
                match=pattern,
                count=100,
            )
            for key in keys:
                payload = self.client.get(key)
                if payload is not None:
                    items.append(parser(payload))
            if int(cursor) == 0:
                break
        return items

    def _assert_result(self, result, operation: str) -> None:
        code = int(result[0])
        if code == -1:
            raise StaleFencingToken(
                f"Bakım journal fencing token eski; {operation} reddedildi"
            )
        if code == 0:
            raise RuntimeError(
                f"Bakım claim sahipliği kaybedildi; {operation} reddedildi"
            )

    def _claim_key(self, claim_id: str) -> str:
        return f"{self.prefix}:claim:{claim_id}"

    def _done_key(self, claim_id: str) -> str:
        return f"{self.prefix}:done:{claim_id}"

    def _quarantine_key(self, claim_id: str) -> str:
        return f"{self.prefix}:quarantine:{claim_id}"

    @staticmethod
    def _serialize(claim: MaintenanceClaim) -> str:
        return json.dumps(
            claim.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _decode(payload) -> str:
        return (
            payload.decode("utf-8")
            if isinstance(payload, bytes)
            else str(payload)
        )

    @classmethod
    def _deserialize_claim(cls, payload) -> MaintenanceClaim:
        data = json.loads(cls._decode(payload))
        return MaintenanceClaim(
            claim_id=str(data["claim_id"]),
            owner_id=str(data.get("owner_id") or "legacy"),
            index_key=str(data["index_key"]),
            phase=str(data["phase"]),
            fencing_token=int(data["fencing_token"]),
            claimed_at=int(data["claimed_at"]),
            heartbeat_at=int(data.get("heartbeat_at", data["claimed_at"])),
            expires_at=int(data["expires_at"]),
            attempts=int(data.get("attempts", 1)),
            status=str(data["status"]),
        )

    @classmethod
    def _deserialize_quarantine(
        cls,
        payload,
    ) -> QuarantinedIndex:
        data = json.loads(cls._decode(payload))
        return QuarantinedIndex(
            claim_id=str(data["claim_id"]),
            index_key=str(data["index_key"]),
            phase=str(data["phase"]),
            attempts=int(data["attempts"]),
            error=str(data["error"]),
            quarantined_at=int(data["quarantined_at"]),
            fencing_token=int(data["fencing_token"]),
        )
