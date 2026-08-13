from __future__ import annotations
import asyncio
import logging

from .quorum_execution import ExecutionOwnershipLost

logger = logging.getLogger(__name__)

class QuorumExecutionHeartbeat:
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
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()
        self._lost = asyncio.Event()

    @property
    def lost(self) -> bool:
        return self._lost.is_set()

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(
                self._run(),
                name="quorum-execution-heartbeat",
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
            except (ExecutionOwnershipLost, KeyError):
                self._lost.set()
                break
            except Exception as exc:
                logger.warning(
                    "Quorum execution heartbeat failed: %s",
                    exc,
                )
