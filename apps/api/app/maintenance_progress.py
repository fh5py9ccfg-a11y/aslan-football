from __future__ import annotations
from dataclasses import dataclass
import json
import time

from .distributed_lease import StaleFencingToken

@dataclass(frozen=True)
class MaintenanceProgress:
    phase: str
    cursor: int
    pending_keys: tuple[str, ...]
    fencing_token: int
    updated_at: int
    completed_cycles: int
    processed_indexes: int

class RedisMaintenanceProgressRepository:
    SAVE_SCRIPT = '''
    local key = KEYS[1]
    local expected = tonumber(ARGV[1])
    local raw = redis.call("GET", key)

    if raw then
        local current = cjson.decode(raw)
        local current_token = tonumber(current.fencing_token or 0)
        if expected < current_token then
            return {-1, current_token}
        end
    end

    redis.call("SET", key, ARGV[2])
    return {1, expected}
    '''

    def __init__(
        self,
        client,
        *,
        key: str = "aslan:maintenance:session-index:progress",
    ):
        self.client = client
        self.key = key

    def load(self) -> MaintenanceProgress:
        payload = self.client.get(self.key)
        if payload is None:
            return self.initial()

        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        return MaintenanceProgress(
            phase=str(data.get("phase") or "subject"),
            cursor=int(data.get("cursor", 0)),
            pending_keys=tuple(
                str(item)
                for item in data.get("pending_keys") or ()
            ),
            fencing_token=int(data.get("fencing_token", 0)),
            updated_at=int(data.get("updated_at", 0)),
            completed_cycles=int(data.get("completed_cycles", 0)),
            processed_indexes=int(data.get("processed_indexes", 0)),
        )

    def initial(self) -> MaintenanceProgress:
        return MaintenanceProgress(
            phase="subject",
            cursor=0,
            pending_keys=(),
            fencing_token=0,
            updated_at=0,
            completed_cycles=0,
            processed_indexes=0,
        )

    def save(
        self,
        progress: MaintenanceProgress,
    ) -> None:
        payload = json.dumps(
            {
                **progress.__dict__,
                "pending_keys": list(progress.pending_keys),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result = self.client.eval(
            self.SAVE_SCRIPT,
            1,
            self.key,
            progress.fencing_token,
            payload,
        )
        if int(result[0]) == -1:
            raise StaleFencingToken(
                "Bakım progress fencing token eski; checkpoint reddedildi"
            )

    def advance(
        self,
        *,
        phase: str,
        cursor: int,
        pending_keys: tuple[str, ...],
        fencing_token: int,
        completed_cycles: int,
        processed_indexes: int,
    ) -> MaintenanceProgress:
        progress = MaintenanceProgress(
            phase=phase,
            cursor=cursor,
            pending_keys=tuple(pending_keys),
            fencing_token=fencing_token,
            updated_at=int(time.time()),
            completed_cycles=completed_cycles,
            processed_indexes=processed_indexes,
        )
        self.save(progress)
        return progress

    def reset(
        self,
        *,
        fencing_token: int,
    ) -> MaintenanceProgress:
        progress = MaintenanceProgress(
            phase="subject",
            cursor=0,
            pending_keys=(),
            fencing_token=fencing_token,
            updated_at=int(time.time()),
            completed_cycles=0,
            processed_indexes=0,
        )
        self.save(progress)
        return progress
