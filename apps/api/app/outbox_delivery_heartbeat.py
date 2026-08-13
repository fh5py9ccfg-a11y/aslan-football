from __future__ import annotations
import asyncio
from dataclasses import dataclass
from .compensation_outbox_publisher import OutboxOwnershipLost

@dataclass(frozen=True)
class GuardedPublishResult:
    receipt: object | None
    ownership_lost: bool
    error: str | None

class OutboxDeliveryHeartbeat:
    def __init__(self, *, repository, record, interval_seconds: float):
        self.repository = repository
        self.record = record
        self.interval_seconds = interval_seconds
        self._stopping = asyncio.Event()
        self._lost = asyncio.Event()
        self._task = None

    @property
    def lost(self):
        return self._lost.is_set()

    async def start(self):
        self._task = asyncio.create_task(self._run())

    async def stop(self):
        self._stopping.set()
        if self._task is not None:
            await self._task

    async def _run(self):
        while not self._stopping.is_set():
            try:
                await asyncio.wait_for(self._stopping.wait(), timeout=self.interval_seconds)
                break
            except asyncio.TimeoutError:
                pass
            try:
                self.record = await asyncio.to_thread(self.repository.heartbeat, self.record)
            except (OutboxOwnershipLost, KeyError):
                self._lost.set()
                break

class OutboxPublishGuard:
    def __init__(self, *, repository, heartbeat_interval_seconds: float):
        self.repository = repository
        self.heartbeat_interval_seconds = heartbeat_interval_seconds

    async def run(self, *, record, operation):
        heartbeat = OutboxDeliveryHeartbeat(
            repository=self.repository,
            record=record,
            interval_seconds=self.heartbeat_interval_seconds,
        )
        await heartbeat.start()
        try:
            receipt = await asyncio.to_thread(operation)
            if heartbeat.lost:
                return GuardedPublishResult(None, True, "Outbox delivery ownership kaybedildi")
            return GuardedPublishResult(receipt, False, None)
        except Exception as exc:
            return GuardedPublishResult(None, False, str(exc))
        finally:
            await heartbeat.stop()
