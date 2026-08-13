from __future__ import annotations
from dataclasses import dataclass
import json
import time

@dataclass(frozen=True)
class IdempotentEffectRecord:
    key: str
    operation: str
    status: str
    owner: str
    started_at: int
    completed_at: int | None
    result_payload: dict | None
    error: str | None

class IdempotentEffectConflict(RuntimeError):
    pass

class RedisIdempotentEffectRepository:
    CLAIM_SCRIPT = '''
    local key = KEYS[1]
    local payload = ARGV[1]
    local ttl = tonumber(ARGV[2])

    local existing = redis.call("GET", key)
    if existing then
        return {0, existing}
    end

    redis.call("SET", key, payload, "EX", ttl)
    return {1, payload}
    '''

    COMPLETE_SCRIPT = '''
    local key = KEYS[1]
    local owner = ARGV[1]
    local payload = ARGV[2]
    local ttl = tonumber(ARGV[3])

    local existing_raw = redis.call("GET", key)
    if not existing_raw then
        return {0, "missing"}
    end

    local existing = cjson.decode(existing_raw)
    if existing.owner ~= owner then
        return {2, existing_raw}
    end

    redis.call("SET", key, payload, "EX", ttl)
    return {1, payload}
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:idempotency",
        ttl_seconds: int = 2_592_000,
    ):
        if ttl_seconds <= 0:
            raise ValueError("idempotency ttl pozitif olmalıdır")
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def claim(
        self,
        *,
        key: str,
        operation: str,
        owner: str,
        now: int | None = None,
    ) -> tuple[bool, IdempotentEffectRecord]:
        current = int(now if now is not None else time.time())
        record = IdempotentEffectRecord(
            key=key,
            operation=operation,
            status="IN_PROGRESS",
            owner=owner,
            started_at=current,
            completed_at=None,
            result_payload=None,
            error=None,
        )
        result = self.client.eval(
            self.CLAIM_SCRIPT,
            1,
            self._key(key),
            self._serialize(record),
            self.ttl_seconds,
        )
        return int(result[0]) == 1, self._deserialize(result[1])

    def complete(
        self,
        *,
        record: IdempotentEffectRecord,
        result_payload: dict,
        now: int | None = None,
    ) -> IdempotentEffectRecord:
        current = int(now if now is not None else time.time())
        completed = IdempotentEffectRecord(
            key=record.key,
            operation=record.operation,
            status="COMPLETED",
            owner=record.owner,
            started_at=record.started_at,
            completed_at=current,
            result_payload=result_payload,
            error=None,
        )
        return self._write_owned(record, completed)

    def fail(
        self,
        *,
        record: IdempotentEffectRecord,
        error: str,
        now: int | None = None,
    ) -> IdempotentEffectRecord:
        current = int(now if now is not None else time.time())
        failed = IdempotentEffectRecord(
            key=record.key,
            operation=record.operation,
            status="FAILED",
            owner=record.owner,
            started_at=record.started_at,
            completed_at=current,
            result_payload=None,
            error=error[:1000],
        )
        return self._write_owned(record, failed)

    def get(self, key: str) -> IdempotentEffectRecord | None:
        payload = self.client.get(self._key(key))
        if payload is None:
            return None
        return self._deserialize(payload)

    def _write_owned(
        self,
        current: IdempotentEffectRecord,
        updated: IdempotentEffectRecord,
    ) -> IdempotentEffectRecord:
        result = self.client.eval(
            self.COMPLETE_SCRIPT,
            1,
            self._key(current.key),
            current.owner,
            self._serialize(updated),
            self.ttl_seconds,
        )
        code = int(result[0])
        if code == 0:
            raise KeyError("Idempotency kaydı bulunamadı")
        if code == 2:
            raise IdempotentEffectConflict(
                "Idempotency kaydı başka owner tarafından yönetiliyor"
            )
        return updated

    def _key(self, key: str) -> str:
        return f"{self.prefix}:{key}"

    @staticmethod
    def _serialize(record: IdempotentEffectRecord) -> str:
        return json.dumps(
            record.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize(payload) -> IdempotentEffectRecord:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return IdempotentEffectRecord(**json.loads(payload))
