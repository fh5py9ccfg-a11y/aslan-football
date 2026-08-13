from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Any
from uuid import uuid4


class JobStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"


@dataclass(frozen=True)
class Job:
    job_id: str
    deduplication_key: str
    status: JobStatus
    created_at: str
    started_at: str | None = None
    finished_at: str | None = None
    error: str | None = None

    @classmethod
    def create(cls, deduplication_key: str) -> "Job":
        if not deduplication_key.strip():
            raise ValueError("deduplication_key zorunludur")
        return cls(
            job_id=str(uuid4()),
            deduplication_key=deduplication_key,
            status=JobStatus.PENDING,
            created_at=datetime.now(timezone.utc).isoformat(),
        )


class JobRunner:
    def __init__(self):
        self._active_keys: set[str] = set()

    def run(self, job: Job, operation: Callable[[], Any]) -> tuple[Job, Any | None]:
        if job.deduplication_key in self._active_keys:
            raise RuntimeError("Aynı iş zaten çalışıyor; yinelenen çalışma engellendi.")

        self._active_keys.add(job.deduplication_key)
        running = replace(
            job,
            status=JobStatus.RUNNING,
            started_at=datetime.now(timezone.utc).isoformat(),
        )
        try:
            result = operation()
            completed = replace(
                running,
                status=JobStatus.SUCCEEDED,
                finished_at=datetime.now(timezone.utc).isoformat(),
            )
            return completed, result
        except Exception as exc:
            failed = replace(
                running,
                status=JobStatus.FAILED,
                finished_at=datetime.now(timezone.utc).isoformat(),
                error=str(exc),
            )
            return failed, None
        finally:
            self._active_keys.remove(job.deduplication_key)
