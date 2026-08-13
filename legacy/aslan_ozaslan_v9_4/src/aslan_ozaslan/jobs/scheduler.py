from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Callable


@dataclass(frozen=True)
class ScheduledTask:
    name: str
    interval_seconds: int
    payload_factory: Callable[[], dict]
    next_run_at: datetime


class IntervalScheduler:
    def __init__(self):
        self._tasks: dict[str, ScheduledTask] = {}

    def register(
        self,
        *,
        name: str,
        interval_seconds: int,
        payload_factory: Callable[[], dict],
        start_at: datetime | None = None,
    ) -> ScheduledTask:
        if not name.strip():
            raise ValueError("Görev adı boş olamaz")
        if interval_seconds <= 0:
            raise ValueError("interval_seconds pozitif olmalıdır")
        if name in self._tasks:
            raise ValueError("Görev zaten kayıtlı")

        task = ScheduledTask(
            name=name,
            interval_seconds=interval_seconds,
            payload_factory=payload_factory,
            next_run_at=start_at or datetime.now(timezone.utc),
        )
        self._tasks[name] = task
        return task

    def due_tasks(self, now: datetime | None = None) -> tuple[ScheduledTask, ...]:
        moment = now or datetime.now(timezone.utc)
        return tuple(
            task for task in self._tasks.values()
            if task.next_run_at <= moment
        )

    def enqueue_due(self, queue, now: datetime | None = None) -> int:
        moment = now or datetime.now(timezone.utc)
        count = 0
        for task in self.due_tasks(moment):
            queue.enqueue(task.name, task.payload_factory())
            self._tasks[task.name] = ScheduledTask(
                name=task.name,
                interval_seconds=task.interval_seconds,
                payload_factory=task.payload_factory,
                next_run_at=moment + timedelta(seconds=task.interval_seconds),
            )
            count += 1
        return count
