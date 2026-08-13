from __future__ import annotations
from dataclasses import dataclass
import asyncio
import logging
import secrets
import time

from .compensation_execution import CompensationOwnershipLost
from .compensation_execution_guard import CompensationExecutionGuard

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class CompensationExecutionResult:
    compensation_id: str
    status: str
    attempts: int
    next_attempt_at: int | None
    error: str | None
    completed_at: int | None
    ownership_lost: bool = False

class CompensationHandlerRegistry:
    def __init__(self):
        self._handlers = {}

    def register(self, action: str, handler) -> None:
        self._handlers[action] = handler

    def get(self, action: str):
        handler = self._handlers.get(action)
        if handler is None:
            raise KeyError(
                f"Compensation handler bulunamadı: {action}"
            )
        return handler

class CompensationOrchestrator:
    def __init__(
        self,
        *,
        repository,
        registry: CompensationHandlerRegistry,
        max_attempts: int = 5,
        base_backoff_seconds: int = 30,
        execution_repository=None,
        heartbeat_interval_seconds: float = 15.0,
        atomic_committer=None,
    ):
        if max_attempts <= 0:
            raise ValueError("max_attempts pozitif olmalıdır")
        if base_backoff_seconds <= 0:
            raise ValueError("base_backoff_seconds pozitif olmalıdır")
        self.repository = repository
        self.registry = registry
        self.max_attempts = max_attempts
        self.base_backoff_seconds = base_backoff_seconds
        self.execution_repository = execution_repository
        self.atomic_committer = atomic_committer
        self.execution_guard = (
            CompensationExecutionGuard(
                repository=execution_repository,
                heartbeat_interval_seconds=heartbeat_interval_seconds,
            )
            if execution_repository is not None
            else None
        )

    def execute(
        self,
        compensation_id: str,
        *,
        now: int | None = None,
    ) -> CompensationExecutionResult:
        return asyncio.run(
            self.execute_async(
                compensation_id,
                now=now,
            )
        )

    async def execute_async(
        self,
        compensation_id: str,
        *,
        now: int | None = None,
    ) -> CompensationExecutionResult:
        current = int(now if now is not None else time.time())
        record = self.repository.get(compensation_id)
        if record is None:
            raise KeyError("Compensation kaydı bulunamadı")

        if record.status == "COMPLETED":
            return CompensationExecutionResult(
                compensation_id=record.compensation_id,
                status="COMPLETED",
                attempts=record.attempts,
                next_attempt_at=None,
                error=None,
                completed_at=record.completed_at,
            )

        if record.status == "DEAD_LETTER":
            return CompensationExecutionResult(
                compensation_id=record.compensation_id,
                status="DEAD_LETTER",
                attempts=record.attempts,
                next_attempt_at=None,
                error=record.reason,
                completed_at=record.completed_at,
            )

        if (
            record.next_attempt_at is not None
            and record.next_attempt_at > current
        ):
            return CompensationExecutionResult(
                compensation_id=record.compensation_id,
                status="SCHEDULED",
                attempts=record.attempts,
                next_attempt_at=record.next_attempt_at,
                error=None,
                completed_at=None,
            )

        execution = None
        if self.execution_repository is not None:
            created, execution = self.execution_repository.claim(
                compensation_id=record.compensation_id,
                owner=secrets.token_urlsafe(12),
                now=current,
            )
            if not created:
                return CompensationExecutionResult(
                    compensation_id=record.compensation_id,
                    status=(
                        "COMPLETED"
                        if execution.status == "COMPLETED"
                        else "IN_PROGRESS"
                    ),
                    attempts=record.attempts,
                    next_attempt_at=None,
                    error=None,
                    completed_at=record.completed_at,
                )

        handler = self.registry.get(record.action)

        if execution is not None and self.execution_guard is not None:
            guarded = await self.execution_guard.run(
                record=execution,
                operation=lambda: handler(record),
            )
            if guarded.ownership_lost:
                return CompensationExecutionResult(
                    compensation_id=record.compensation_id,
                    status="OWNERSHIP_LOST",
                    attempts=record.attempts,
                    next_attempt_at=None,
                    error=guarded.error,
                    completed_at=None,
                    ownership_lost=True,
                )
            handler_error = guarded.error
        else:
            try:
                await asyncio.to_thread(handler, record)
                handler_error = None
            except Exception as exc:
                handler_error = str(exc)

        if handler_error is None:
            try:
                if (
                    self.atomic_committer is not None
                    and execution is not None
                ):
                    self.atomic_committer.commit_success(
                        compensation=record,
                        execution=execution,
                        result_payload={"status": "COMPLETED"},
                        now=current,
                    )
                    updated = self.repository.get(
                        record.compensation_id
                    )
                else:
                    if (
                        self.execution_repository is not None
                        and execution is not None
                    ):
                        self.execution_repository.complete(execution)

                    updated = self.repository.mark_completed(
                        record,
                        now=current,
                    )
                return CompensationExecutionResult(
                    compensation_id=updated.compensation_id,
                    status=updated.status,
                    attempts=updated.attempts,
                    next_attempt_at=None,
                    error=None,
                    completed_at=updated.completed_at,
                )
            except CompensationOwnershipLost as exc:
                return CompensationExecutionResult(
                    compensation_id=record.compensation_id,
                    status="OWNERSHIP_LOST",
                    attempts=record.attempts,
                    next_attempt_at=None,
                    error=str(exc),
                    completed_at=None,
                    ownership_lost=True,
                )

        attempts = record.attempts + 1
        if attempts >= self.max_attempts:
            updated = self.repository.mark_dead_letter(
                record,
                reason=handler_error,
                now=current,
            )
            return CompensationExecutionResult(
                compensation_id=updated.compensation_id,
                status=updated.status,
                attempts=updated.attempts,
                next_attempt_at=None,
                error=updated.reason,
                completed_at=updated.completed_at,
            )

        delay = self.base_backoff_seconds * (2 ** (attempts - 1))
        updated = self.repository.schedule_retry(
            record,
            reason=handler_error,
            next_attempt_at=current + delay,
        )
        return CompensationExecutionResult(
            compensation_id=updated.compensation_id,
            status=updated.status,
            attempts=updated.attempts,
            next_attempt_at=updated.next_attempt_at,
            error=updated.reason,
            completed_at=None,
        )

class CompensationWorker:
    def __init__(
        self,
        *,
        repository,
        orchestrator: CompensationOrchestrator,
        interval_seconds: float = 30.0,
        batch_size: int = 50,
    ):
        if interval_seconds <= 0 or batch_size <= 0:
            raise ValueError("Worker ayarları pozitif olmalıdır")
        self.repository = repository
        self.orchestrator = orchestrator
        self.interval_seconds = interval_seconds
        self.batch_size = batch_size
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()
        self.last_results = []

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(
                self._run(),
                name="compensation-worker",
            )

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def run_once(self):
        due = self.repository.list_due(
            limit=self.batch_size,
        )
        results = []
        for record in due:
            try:
                execute_async = getattr(
                    self.orchestrator,
                    "execute_async",
                    None,
                )
                if callable(execute_async):
                    result = await execute_async(
                        record.compensation_id,
                    )
                else:
                    result = await asyncio.to_thread(
                        self.orchestrator.execute,
                        record.compensation_id,
                    )
                results.append(result)
            except Exception as exc:
                logger.warning(
                    "Compensation execution failed: %s",
                    exc,
                )
        self.last_results = results
        return tuple(results)

    async def _run(self) -> None:
        while not self._stopping.is_set():
            await self.run_once()
            try:
                await asyncio.wait_for(
                    self._stopping.wait(),
                    timeout=self.interval_seconds,
                )
            except asyncio.TimeoutError:
                pass
