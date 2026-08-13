from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any

from .persistent_queue import SQLiteJobQueue, PersistentJob


@dataclass(frozen=True)
class WorkerResult:
    processed: bool
    job_id: str | None
    status: str | None


class JobWorker:
    def __init__(
        self,
        queue: SQLiteJobQueue,
        handlers: dict[str, Callable[[dict[str, Any]], Any]],
        worker_id: str,
    ):
        self.queue = queue
        self.handlers = handlers
        self.worker_id = worker_id

    def run_once(self) -> WorkerResult:
        job = self.queue.claim_next(self.worker_id)
        if job is None:
            return WorkerResult(False, None, None)

        handler = self.handlers.get(job.name)
        if handler is None:
            self.queue.mark_failed(job.job_id, self.worker_id, "Handler bulunamadı")
            current = self.queue.get(job.job_id)
            return WorkerResult(True, job.job_id, current.status)

        try:
            handler(job.payload)
        except Exception as exc:
            self.queue.mark_failed(job.job_id, self.worker_id, str(exc))
        else:
            self.queue.mark_succeeded(job.job_id, self.worker_id)

        current = self.queue.get(job.job_id)
        return WorkerResult(True, job.job_id, current.status)
