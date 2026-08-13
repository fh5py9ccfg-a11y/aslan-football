from __future__ import annotations
import asyncio
from dataclasses import dataclass

from .compensation_execution import CompensationOwnershipLost

@dataclass(frozen=True)
class GuardedCompensationResult:
    result: object | None
    ownership_lost: bool
    error: str | None

class CompensationExecutionHeartbeat:
    def __init__(
        self,
        *,
        repository,
        record,
        interval_seconds: float,
    ):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds pozitif olmalıdır")
        self.repository = repository
        self.record = record
        self.interval_seconds = interval_seconds
        self._stopping = asyncio.Event()
        self._lost = asyncio.Event()
        self._task: asyncio.Task | None = None

    @property
    def lost(self) -> bool:
        return self._lost.is_set()

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(
                self._run(),
                name="compensation-execution-heartbeat",
            )

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def _run(self) -> None:
        while not self._stopping.is_set():
            try:
                await asyncio.wait_for(
                    self._stopping.wait(),
                    timeout=self.interval_seconds,
                )
                break
            except asyncio.TimeoutError:
                pass

            try:
                self.record = await asyncio.to_thread(
                    self.repository.heartbeat,
                    self.record,
                )
            except (CompensationOwnershipLost, KeyError):
                self._lost.set()
                break

class CompensationExecutionGuard:
    def __init__(
        self,
        *,
        repository,
        heartbeat_interval_seconds: float,
    ):
        if heartbeat_interval_seconds <= 0:
            raise ValueError(
                "heartbeat_interval_seconds pozitif olmalıdır"
            )
        self.repository = repository
        self.heartbeat_interval_seconds = heartbeat_interval_seconds

    async def run(
        self,
        *,
        record,
        operation,
    ) -> GuardedCompensationResult:
        heartbeat = CompensationExecutionHeartbeat(
            repository=self.repository,
            record=record,
            interval_seconds=self.heartbeat_interval_seconds,
        )
        await heartbeat.start()
        try:
            result = await asyncio.to_thread(operation)

            if heartbeat.lost:
                return GuardedCompensationResult(
                    result=None,
                    ownership_lost=True,
                    error="Compensation execution ownership kaybedildi",
                )

            return GuardedCompensationResult(
                result=result,
                ownership_lost=False,
                error=None,
            )
        except CompensationOwnershipLost as exc:
            return GuardedCompensationResult(
                result=None,
                ownership_lost=True,
                error=str(exc),
            )
        except Exception as exc:
            return GuardedCompensationResult(
                result=None,
                ownership_lost=False,
                error=str(exc),
            )
        finally:
            await heartbeat.stop()
