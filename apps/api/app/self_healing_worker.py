from __future__ import annotations

import asyncio
import logging


logger = logging.getLogger(__name__)


class SelfHealingWorker:
    def __init__(
        self,
        *,
        orchestrator,
        interval_seconds: float = 30.0,
    ):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds pozitif olmalıdır")
        self.orchestrator = orchestrator
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()
        self.last_actions = ()

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(
                self._run(),
                name="self-healing-worker",
            )

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def run_once(self):
        self.last_actions = await asyncio.to_thread(
            self.orchestrator.reconcile
        )
        return self.last_actions

    async def _run(self) -> None:
        while not self._stopping.is_set():
            try:
                await self.run_once()
            except Exception as exc:
                logger.warning("Self-healing cycle failed: %s", exc)

            try:
                await asyncio.wait_for(
                    self._stopping.wait(),
                    timeout=self.interval_seconds,
                )
            except asyncio.TimeoutError:
                pass
