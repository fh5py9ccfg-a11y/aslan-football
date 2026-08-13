from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class OutboxMessage:
    message_id: str
    aggregate_id: str
    topic: str
    payload: dict
    status: str
    attempt_count: int
    available_at: str
    lease_owner: str | None = None
    lease_until: str | None = None
    last_error: str | None = None

@dataclass(frozen=True)
class WorkerBatchReport:
    worker_id: str
    claimed: int
    published: int
    retried: int
    dead_lettered: int
