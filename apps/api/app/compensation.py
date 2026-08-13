from __future__ import annotations
from dataclasses import dataclass
import json
import secrets
import time

@dataclass(frozen=True)
class CompensationRecord:
    compensation_id: str
    request_id: str
    claim_id: str
    action: str
    status: str
    reason: str
    created_at: int
    completed_at: int | None
    attempts: int
    next_attempt_at: int | None = None

class RedisCompensationRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:compensation",
        ttl_seconds: int = 2_592_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def create(
        self,
        *,
        request_id: str,
        claim_id: str,
        action: str,
        reason: str,
        now: int | None = None,
    ) -> CompensationRecord:
        current = int(now if now is not None else time.time())
        record = CompensationRecord(
            compensation_id=secrets.token_urlsafe(18),
            request_id=request_id,
            claim_id=claim_id,
            action=action,
            status="PENDING",
            reason=reason[:1000],
            created_at=current,
            completed_at=None,
            attempts=0,
            next_attempt_at=current,
        )
        self._save(record)
        self.client.sadd(
            self._request_index(request_id),
            record.compensation_id,
        )
        self.client.sadd(
            self._status_index("PENDING"),
            record.compensation_id,
        )
        return record

    def mark_completed(
        self,
        record: CompensationRecord,
        *,
        now: int | None = None,
    ) -> CompensationRecord:
        current = int(now if now is not None else time.time())
        updated = CompensationRecord(
            **{
                **record.__dict__,
                "status": "COMPLETED",
                "completed_at": current,
                "attempts": record.attempts + 1,
                "next_attempt_at": None,
            }
        )
        self._move_status(record.status, updated.status, record.compensation_id)
        self._save(updated)
        return updated

    def mark_dead_letter(
        self,
        record: CompensationRecord,
        *,
        reason: str,
        now: int | None = None,
    ) -> CompensationRecord:
        current = int(now if now is not None else time.time())
        updated = CompensationRecord(
            **{
                **record.__dict__,
                "status": "DEAD_LETTER",
                "reason": reason[:1000],
                "completed_at": current,
                "attempts": record.attempts + 1,
                "next_attempt_at": None,
            }
        )
        self._move_status(record.status, updated.status, record.compensation_id)
        self._save(updated)
        return updated

    def schedule_retry(
        self,
        record: CompensationRecord,
        *,
        reason: str,
        next_attempt_at: int,
    ) -> CompensationRecord:
        updated = CompensationRecord(
            **{
                **record.__dict__,
                "status": "RETRY_SCHEDULED",
                "reason": reason[:1000],
                "attempts": record.attempts + 1,
                "next_attempt_at": next_attempt_at,
            }
        )
        self._move_status(record.status, updated.status, record.compensation_id)
        self._save(updated)
        return updated

    def requeue(
        self,
        record: CompensationRecord,
        *,
        now: int | None = None,
    ) -> CompensationRecord:
        current = int(now if now is not None else time.time())
        updated = CompensationRecord(
            **{
                **record.__dict__,
                "status": "PENDING",
                "completed_at": None,
                "next_attempt_at": current,
            }
        )
        self._move_status(record.status, updated.status, record.compensation_id)
        self._save(updated)
        return updated

    def get(self, compensation_id: str) -> CompensationRecord | None:
        payload = self.client.get(self._key(compensation_id))
        if payload is None:
            return None
        return self._deserialize(payload)

    def list_request(self, request_id: str) -> tuple[CompensationRecord, ...]:
        ids = self.client.smembers(self._request_index(request_id))
        return self._load_many(ids)

    def list_due(
        self,
        *,
        limit: int = 50,
        now: int | None = None,
    ) -> tuple[CompensationRecord, ...]:
        current = int(now if now is not None else time.time())
        ids = set()
        for status in ("PENDING", "RETRY_SCHEDULED"):
            ids.update(
                self.client.smembers(
                    self._status_index(status)
                )
            )

        items = []
        for item in self._load_many(ids):
            if (
                item.next_attempt_at is None
                or item.next_attempt_at <= current
            ):
                items.append(item)
        items.sort(
            key=lambda item: (
                item.next_attempt_at or 0,
                item.created_at,
            )
        )
        return tuple(items[:limit])

    def _load_many(self, ids) -> tuple[CompensationRecord, ...]:
        items = []
        for item_id in ids:
            if isinstance(item_id, bytes):
                item_id = item_id.decode("utf-8")
            item = self.get(str(item_id))
            if item is not None:
                items.append(item)
        return tuple(
            sorted(
                items,
                key=lambda item: item.created_at,
                reverse=True,
            )
        )

    def _move_status(
        self,
        old_status: str,
        new_status: str,
        compensation_id: str,
    ) -> None:
        if old_status:
            self.client.srem(
                self._status_index(old_status),
                compensation_id,
            )
        self.client.sadd(
            self._status_index(new_status),
            compensation_id,
        )

    def _save(self, record: CompensationRecord) -> None:
        self.client.setex(
            self._key(record.compensation_id),
            self.ttl_seconds,
            self._serialize(record),
        )

    def _key(self, compensation_id: str) -> str:
        return f"{self.prefix}:record:{compensation_id}"

    def _request_index(self, request_id: str) -> str:
        return f"{self.prefix}:request:{request_id}"

    def _status_index(self, status: str) -> str:
        return f"{self.prefix}:status:{status}"

    @staticmethod
    def _serialize(record: CompensationRecord) -> str:
        return json.dumps(
            record.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize(payload) -> CompensationRecord:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        return CompensationRecord(
            compensation_id=str(data["compensation_id"]),
            request_id=str(data["request_id"]),
            claim_id=str(data["claim_id"]),
            action=str(data["action"]),
            status=str(data["status"]),
            reason=str(data["reason"]),
            created_at=int(data["created_at"]),
            completed_at=(
                int(data["completed_at"])
                if data.get("completed_at") is not None
                else None
            ),
            attempts=int(data.get("attempts", 0)),
            next_attempt_at=(
                int(data["next_attempt_at"])
                if data.get("next_attempt_at") is not None
                else None
            ),
        )
