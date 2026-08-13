from dataclasses import dataclass
import json
import time

from .distributed_lease import StaleFencingToken
from .maintenance_progress import MaintenanceProgress

@dataclass(frozen=True)
class QuarantineAction:
    claim_id: str
    index_key: str
    phase: str
    action: str
    operator: str
    note: str
    fencing_token: int
    created_at: int

class RedisQuarantineManager:
    RELEASE_SCRIPT = '''
    local quarantine_key = KEYS[1]
    local audit_key = KEYS[2]
    local fence_key = KEYS[3]
    local token = tonumber(ARGV[1])
    local audit_payload = ARGV[2]
    local audit_ttl = tonumber(ARGV[3])

    local current = tonumber(redis.call("GET", fence_key) or "0")
    if token < current then
        return {-1, current}
    end

    if redis.call("EXISTS", quarantine_key) == 0 then
        return {0, "missing"}
    end

    redis.call("SET", fence_key, token)
    redis.call("DEL", quarantine_key)
    redis.call("SET", audit_key, audit_payload, "EX", audit_ttl)
    return {1, token}
    '''

    def __init__(
        self,
        client,
        *,
        journal_prefix="aslan:maintenance:journal",
        fence_key="aslan:maintenance:session-index:fence",
        audit_ttl_seconds=2592000,
    ):
        self.client = client
        self.journal_prefix = journal_prefix
        self.fence_key = fence_key
        self.audit_ttl_seconds = audit_ttl_seconds

    def release(
        self,
        *,
        claim_id,
        operator,
        note,
        fencing_token,
        now=None,
    ):
        quarantine_key = self._quarantine_key(claim_id)
        raw = self.client.get(quarantine_key)
        if raw is None:
            raise KeyError("Karantina kaydı bulunamadı")
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        quarantine = json.loads(raw)

        current = int(now if now is not None else time.time())
        item = QuarantineAction(
            claim_id=claim_id,
            index_key=str(quarantine["index_key"]),
            phase=str(quarantine["phase"]),
            action="RELEASE",
            operator=operator,
            note=note[:1000],
            fencing_token=fencing_token,
            created_at=current,
        )
        payload = json.dumps(
            item.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result = self.client.eval(
            self.RELEASE_SCRIPT,
            3,
            quarantine_key,
            self._audit_key(claim_id, current),
            self.fence_key,
            fencing_token,
            payload,
            self.audit_ttl_seconds,
        )
        code = int(result[0])
        if code == -1:
            raise StaleFencingToken(
                "Karantina işlemi stale fencing token nedeniyle reddedildi"
            )
        if code == 0:
            raise KeyError("Karantina kaydı bulunamadı")
        return item

    def requeue(
        self,
        *,
        action,
        progress_repository,
    ):
        progress = progress_repository.load()
        pending = list(progress.pending_keys)
        if action.index_key not in pending:
            pending.insert(0, action.index_key)
        updated = MaintenanceProgress(
            phase=action.phase,
            cursor=progress.cursor,
            pending_keys=tuple(pending),
            fencing_token=action.fencing_token,
            updated_at=int(time.time()),
            completed_cycles=progress.completed_cycles,
            processed_indexes=progress.processed_indexes,
        )
        progress_repository.save(updated)
        return updated

    def history(self, claim_id):
        items = []
        cursor = 0
        while True:
            cursor, keys = self.client.scan(
                cursor=cursor,
                match=f"{self.journal_prefix}:audit:{claim_id}:*",
                count=100,
            )
            for key in keys:
                payload = self.client.get(key)
                if payload is None:
                    continue
                if isinstance(payload, bytes):
                    payload = payload.decode("utf-8")
                data = json.loads(payload)
                items.append(QuarantineAction(**data))
            if int(cursor) == 0:
                break
        return tuple(sorted(items, key=lambda x: x.created_at, reverse=True))

    def _quarantine_key(self, claim_id):
        return f"{self.journal_prefix}:quarantine:{claim_id}"

    def _audit_key(self, claim_id, created_at):
        return f"{self.journal_prefix}:audit:{claim_id}:{created_at}"
