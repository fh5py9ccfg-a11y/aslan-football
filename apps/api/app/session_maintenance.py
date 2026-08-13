from __future__ import annotations
from dataclasses import dataclass
import asyncio
import logging
import random
import time

from .distributed_lease import LeaseLost, StaleFencingToken
from .fenced_redis import FencedRedisMutator
from .maintenance_journal import RedisMaintenanceJournal
from .maintenance_progress import (
    MaintenanceProgress,
)

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class SessionIndexMaintenanceReport:
    subject_indexes_scanned: int
    family_indexes_scanned: int
    orphan_members_removed: int
    ttl_repairs: int
    errors: int
    duration_ms: float = 0.0
    lease_acquired: bool = True
    lease_lost: bool = False
    aborted: bool = False
    fencing_token: int = 0
    stale_write_rejected: bool = False
    budget_exhausted: bool = False
    batch_limit_reached: bool = False
    next_phase: str = "subject"
    next_cursor: int = 0
    pending_keys: int = 0
    completed_cycles: int = 0
    processed_indexes: int = 0
    quarantined_indexes: int = 0

class RedisSessionIndexMaintainer:
    PHASES = ("subject", "family")

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:refresh",
        checkpoint=None,
        mutator=None,
        progress_repository=None,
        max_indexes_per_run: int = 500,
        time_budget_seconds: float = 20.0,
        scan_count: int = 100,
        journal=None,
    ):
        if max_indexes_per_run <= 0:
            raise ValueError("max_indexes_per_run pozitif olmalıdır")
        if time_budget_seconds <= 0:
            raise ValueError("time_budget_seconds pozitif olmalıdır")
        if scan_count <= 0:
            raise ValueError("scan_count pozitif olmalıdır")

        self.client = client
        self.prefix = prefix
        self.checkpoint = checkpoint
        self.mutator = mutator
        self.progress_repository = progress_repository
        self.max_indexes_per_run = max_indexes_per_run
        self.time_budget_seconds = time_budget_seconds
        self.scan_count = scan_count
        self.journal = journal

    def run_once(self) -> SessionIndexMaintenanceReport:
        started = time.perf_counter()
        progress = self._load_progress()
        phase = (
            progress.phase
            if progress.phase in self.PHASES
            else "subject"
        )
        cursor = progress.cursor
        pending_keys = list(progress.pending_keys)
        completed_cycles = progress.completed_cycles
        processed_total = progress.processed_indexes

        subject_scanned = 0
        family_scanned = 0
        orphan_removed = 0
        ttl_repairs = 0
        errors = 0
        processed_this_run = 0
        quarantined_indexes = 0
        fencing_token = (
            self.mutator.fencing_token
            if self.mutator is not None
            else progress.fencing_token
        )
        budget_exhausted = False
        batch_limit_reached = False

        try:
            while True:
                self._checkpoint()

                if self._budget_reached(started):
                    budget_exhausted = True
                    break

                if processed_this_run >= self.max_indexes_per_run:
                    batch_limit_reached = True
                    break

                if not pending_keys:
                    pattern = (
                        f"{self.prefix}:subject:*"
                        if phase == "subject"
                        else f"{self.prefix}:family:*"
                    )
                    try:
                        next_cursor, keys = self.client.scan(
                            cursor=cursor,
                            match=pattern,
                            count=self.scan_count,
                        )
                    except Exception:
                        errors += 1
                        break

                    cursor = int(next_cursor)
                    pending_keys = [
                        self._decode(key)
                        for key in keys
                    ]
                    self._save_progress(
                        phase=phase,
                        cursor=cursor,
                        pending_keys=tuple(pending_keys),
                        fencing_token=fencing_token,
                        completed_cycles=completed_cycles,
                        processed_indexes=processed_total,
                    )

                while pending_keys:
                    self._checkpoint()

                    if self._budget_reached(started):
                        budget_exhausted = True
                        break

                    if processed_this_run >= self.max_indexes_per_run:
                        batch_limit_reached = True
                        break

                    key = pending_keys[0]
                    claim_id = self._claim_id(
                        phase=phase,
                        index_key=key,
                    )

                    if (
                        self.journal is not None
                        and (
                            self.journal.is_completed(
                                claim_id
                            )
                            or (
                                getattr(
                                    self.journal,
                                    "is_quarantined",
                                    lambda value: False,
                                )(claim_id)
                            )
                        )
                    ):
                        pending_keys.pop(0)
                        processed_this_run += 1
                        processed_total += 1
                        self._save_progress(
                            phase=phase,
                            cursor=cursor,
                            pending_keys=tuple(
                                pending_keys
                            ),
                            fencing_token=(
                                fencing_token
                            ),
                            completed_cycles=(
                                completed_cycles
                            ),
                            processed_indexes=(
                                processed_total
                            ),
                        )
                        continue

                    claim = None
                    if self.journal is not None:
                        try:
                            claim = self.journal.claim(
                                claim_id=claim_id,
                                index_key=key,
                                phase=phase,
                                fencing_token=(
                                    fencing_token
                                ),
                                owner_id=(
                                    str(fencing_token)
                                    + ":"
                                    + claim_id[:12]
                                ),
                            )
                        except TypeError:
                            claim = self.journal.claim(
                                claim_id=claim_id,
                                index_key=key,
                                phase=phase,
                                fencing_token=(
                                    fencing_token
                                ),
                            )
                        if claim is None:
                            break

                    if phase == "subject":
                        subject_scanned += 1
                    else:
                        family_scanned += 1

                    removed = 0
                    repaired = 0
                    try:
                        removed, repaired = (
                            self._clean_index(key)
                        )
                        orphan_removed += removed
                        ttl_repairs += repaired

                        if (
                            self.journal is not None
                            and claim is not None
                        ):
                            self.journal.complete(
                                claim=claim,
                                removed=removed,
                                repaired=repaired,
                            )
                    except (
                        LeaseLost,
                        StaleFencingToken,
                    ):
                        raise
                    except Exception as exc:
                        errors += 1
                        if (
                            self.journal is not None
                            and claim is not None
                            and getattr(
                                self.journal,
                                "should_quarantine",
                                lambda item: False,
                            )(claim)
                        ):
                            self.journal.quarantine(
                                claim=claim,
                                error=str(exc),
                            )
                            quarantined_indexes += 1
                        else:
                            break

                    if (
                        self.journal is not None
                        and claim is not None
                        and not self.journal.is_completed(
                            claim.claim_id
                        )
                        and not getattr(
                            self.journal,
                            "is_quarantined",
                            lambda value: False,
                        )(claim.claim_id)
                    ):
                        break

                    pending_keys.pop(0)
                    processed_this_run += 1
                    processed_total += 1

                    self._save_progress(
                        phase=phase,
                        cursor=cursor,
                        pending_keys=tuple(pending_keys),
                        fencing_token=fencing_token,
                        completed_cycles=completed_cycles,
                        processed_indexes=processed_total,
                    )

                if (
                    budget_exhausted
                    or batch_limit_reached
                ):
                    break

                if pending_keys:
                    continue

                if cursor == 0:
                    if phase == "subject":
                        phase = "family"
                    else:
                        phase = "subject"
                        completed_cycles += 1

                    cursor = 0
                    self._save_progress(
                        phase=phase,
                        cursor=0,
                        pending_keys=(),
                        fencing_token=fencing_token,
                        completed_cycles=completed_cycles,
                        processed_indexes=processed_total,
                    )

                    if phase == "subject":
                        break

        except LeaseLost:
            return self._report(
                started=started,
                subject_scanned=subject_scanned,
                family_scanned=family_scanned,
                orphan_removed=orphan_removed,
                ttl_repairs=ttl_repairs,
                errors=errors,
                fencing_token=fencing_token,
                lease_lost=True,
                aborted=True,
                stale_write_rejected=False,
                budget_exhausted=budget_exhausted,
                batch_limit_reached=batch_limit_reached,
                phase=phase,
                cursor=cursor,
                pending_keys=pending_keys,
                completed_cycles=completed_cycles,
                processed_indexes=processed_total,
                quarantined_indexes=quarantined_indexes,
            )
        except StaleFencingToken:
            return self._report(
                started=started,
                subject_scanned=subject_scanned,
                family_scanned=family_scanned,
                orphan_removed=orphan_removed,
                ttl_repairs=ttl_repairs,
                errors=errors,
                fencing_token=fencing_token,
                lease_lost=True,
                aborted=True,
                stale_write_rejected=True,
                budget_exhausted=budget_exhausted,
                batch_limit_reached=batch_limit_reached,
                phase=phase,
                cursor=cursor,
                pending_keys=pending_keys,
                completed_cycles=completed_cycles,
                processed_indexes=processed_total,
                quarantined_indexes=quarantined_indexes,
            )

        return self._report(
            started=started,
            subject_scanned=subject_scanned,
            family_scanned=family_scanned,
            orphan_removed=orphan_removed,
            ttl_repairs=ttl_repairs,
            errors=errors,
            fencing_token=fencing_token,
            lease_lost=False,
            aborted=False,
            stale_write_rejected=False,
            budget_exhausted=budget_exhausted,
            batch_limit_reached=batch_limit_reached,
            phase=phase,
            cursor=cursor,
            pending_keys=pending_keys,
            completed_cycles=completed_cycles,
            processed_indexes=processed_total,
            quarantined_indexes=quarantined_indexes,
        )

    def _load_progress(self) -> MaintenanceProgress:
        if self.progress_repository is None:
            return MaintenanceProgress(
                phase="subject",
                cursor=0,
                pending_keys=(),
                fencing_token=0,
                updated_at=0,
                completed_cycles=0,
                processed_indexes=0,
            )
        return self.progress_repository.load()

    def _save_progress(
        self,
        *,
        phase,
        cursor,
        pending_keys,
        fencing_token,
        completed_cycles,
        processed_indexes,
    ) -> None:
        if self.progress_repository is None:
            return
        self.progress_repository.advance(
            phase=phase,
            cursor=cursor,
            pending_keys=tuple(pending_keys),
            fencing_token=fencing_token,
            completed_cycles=completed_cycles,
            processed_indexes=processed_indexes,
        )

    def _budget_reached(
        self,
        started: float,
    ) -> bool:
        return (
            time.perf_counter() - started
            >= self.time_budget_seconds
        )

    def _checkpoint(self) -> None:
        if self.checkpoint is not None:
            self.checkpoint()

    def _clean_index(self, index_key) -> tuple[int, int]:
        members = self.client.smembers(index_key)
        removed = 0
        max_ttl = 0

        for session_id in members:
            self._checkpoint()
            session_id = self._decode(session_id)
            session_key = (
                f"{self.prefix}:session:{session_id}"
            )
            ttl = int(self.client.ttl(session_key))

            if ttl <= 0:
                if self.mutator is not None:
                    removed += self.mutator.remove_orphan(
                        index_key,
                        session_id,
                    )
                else:
                    removed += int(
                        self.client.srem(
                            index_key,
                            session_id,
                        )
                    )
            else:
                max_ttl = max(max_ttl, ttl)

        repaired = 0
        index_ttl = int(self.client.ttl(index_key))

        if not members:
            if self.mutator is not None:
                self.mutator.delete_index(index_key)
            else:
                self.client.delete(index_key)
            return removed, repaired

        if max_ttl > 0 and (
            index_ttl < 0
            or index_ttl < max_ttl
        ):
            if self.mutator is not None:
                repaired = self.mutator.expire_index(
                    index_key,
                    max_ttl,
                )
            else:
                repaired = int(
                    self.client.expire(
                        index_key,
                        max_ttl,
                    )
                )

        return removed, repaired

    def _report(
        self,
        *,
        started,
        subject_scanned,
        family_scanned,
        orphan_removed,
        ttl_repairs,
        errors,
        fencing_token,
        lease_lost,
        aborted,
        stale_write_rejected,
        budget_exhausted,
        batch_limit_reached,
        phase,
        cursor,
        pending_keys,
        completed_cycles,
        processed_indexes,
        quarantined_indexes,
    ) -> SessionIndexMaintenanceReport:
        return SessionIndexMaintenanceReport(
            subject_indexes_scanned=subject_scanned,
            family_indexes_scanned=family_scanned,
            orphan_members_removed=orphan_removed,
            ttl_repairs=ttl_repairs,
            errors=errors,
            duration_ms=(
                time.perf_counter() - started
            ) * 1000,
            lease_acquired=True,
            lease_lost=lease_lost,
            aborted=aborted,
            fencing_token=fencing_token,
            stale_write_rejected=stale_write_rejected,
            budget_exhausted=budget_exhausted,
            batch_limit_reached=batch_limit_reached,
            next_phase=phase,
            next_cursor=cursor,
            pending_keys=len(pending_keys),
            completed_cycles=completed_cycles,
            processed_indexes=processed_indexes,
            quarantined_indexes=quarantined_indexes,
        )

    @staticmethod
    def _claim_id(
        *,
        phase: str,
        index_key: str,
    ) -> str:
        import hashlib

        digest = hashlib.sha256(
            f"{phase}:{index_key}".encode(
                "utf-8"
            )
        ).hexdigest()
        return digest

    @staticmethod
    def _decode(value) -> str:
        return (
            value.decode("utf-8")
            if isinstance(value, bytes)
            else str(value)
        )

class LeaseHeartbeat:
    def __init__(
        self,
        *,
        lease,
        interval_seconds: float,
    ):
        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds pozitif olmalıdır"
            )
        self.lease = lease
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
                name="session-maintenance-lease-heartbeat",
            )

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await self._task
            self._task = None

    def checkpoint(self) -> None:
        if self.lost:
            raise LeaseLost(
                "Dağıtık lease kaybedildi"
            )

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
                renewed = self.lease.renew()
            except Exception:
                renewed = False

            if not renewed:
                self._lost.set()
                break

class SessionMaintenanceWorker:
    def __init__(
        self,
        *,
        maintainer,
        interval_seconds: float = 300.0,
        lease=None,
        lease_heartbeat_seconds: float | None = None,
        jitter_seconds: float = 5.0,
        error_backoff_seconds: float = 30.0,
        metrics=None,
        fence_key: str = (
            "aslan:maintenance:session-index:fence"
        ),
    ):
        if interval_seconds <= 0:
            raise ValueError(
                "interval_seconds pozitif olmalıdır"
            )
        self.maintainer = maintainer
        self.interval_seconds = interval_seconds
        self.lease = lease
        self.lease_heartbeat_seconds = (
            lease_heartbeat_seconds
        )
        self.jitter_seconds = jitter_seconds
        self.error_backoff_seconds = (
            error_backoff_seconds
        )
        self.metrics = metrics
        self.fence_key = fence_key
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()
        self.last_report = None
        self.last_error: str | None = None

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(
                self._run(),
                name="session-index-maintenance",
            )

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def run_once(self):
        lease_acquired = (
            self.lease.acquire()
            if self.lease is not None
            else True
        )
        heartbeat = None

        if not lease_acquired:
            report = SessionIndexMaintenanceReport(
                subject_indexes_scanned=0,
                family_indexes_scanned=0,
                orphan_members_removed=0,
                ttl_repairs=0,
                errors=0,
                lease_acquired=False,
            )
            self.last_report = report
            self._metric(
                "aslan_session_maintenance_skipped_total"
            )
            return report

        try:
            fencing_token = int(
                getattr(
                    self.lease,
                    "fencing_token",
                    0,
                )
            ) if self.lease is not None else 0

            if (
                fencing_token > 0
                and hasattr(
                    self.maintainer,
                    "client",
                )
            ):
                self.maintainer.mutator = (
                    FencedRedisMutator(
                        self.maintainer.client,
                        fencing_token=fencing_token,
                        fence_key=self.fence_key,
                    )
                )

            if (
                self.lease is not None
                and self.lease_heartbeat_seconds
                is not None
            ):
                heartbeat = LeaseHeartbeat(
                    lease=self.lease,
                    interval_seconds=(
                        self.lease_heartbeat_seconds
                    ),
                )
                await heartbeat.start()
                self.maintainer.checkpoint = (
                    heartbeat.checkpoint
                )

            report = await asyncio.to_thread(
                self.maintainer.run_once
            )
            self.last_report = report
            self.last_error = None

            self._metric(
                "aslan_session_maintenance_runs_total"
            )
            self._metric(
                "aslan_session_maintenance_orphans_removed_total",
                report.orphan_members_removed,
            )
            self._metric(
                "aslan_session_maintenance_ttl_repairs_total",
                report.ttl_repairs,
            )
            self._metric(
                "aslan_session_maintenance_errors_total",
                report.errors,
            )
            if report.lease_lost:
                self._metric(
                    "aslan_session_maintenance_lease_lost_total"
                )
            if report.aborted:
                self._metric(
                    "aslan_session_maintenance_aborted_total"
                )
            if report.budget_exhausted:
                self._metric(
                    "aslan_session_maintenance_budget_exhausted_total"
                )
            if report.batch_limit_reached:
                self._metric(
                    "aslan_session_maintenance_batch_limit_total"
                )
            if report.quarantined_indexes:
                self._metric(
                    "aslan_session_maintenance_quarantined_total",
                    report.quarantined_indexes,
                )
            if report.stale_write_rejected:
                self._metric(
                    "aslan_session_maintenance_stale_write_rejected_total"
                )
            return report

        except Exception as exc:
            self.last_error = str(exc)
            self._metric(
                "aslan_session_maintenance_failures_total"
            )
            raise

        finally:
            if heartbeat is not None:
                await heartbeat.stop()
                self.maintainer.checkpoint = None
            self.maintainer.mutator = None
            if self.lease is not None:
                self.lease.release()

    async def _run(self) -> None:
        while not self._stopping.is_set():
            delay = self.interval_seconds
            try:
                await self.run_once()
                if self.jitter_seconds:
                    delay += random.uniform(
                        0,
                        self.jitter_seconds,
                    )
            except Exception:
                delay = self.error_backoff_seconds

            try:
                await asyncio.wait_for(
                    self._stopping.wait(),
                    timeout=delay,
                )
            except asyncio.TimeoutError:
                pass

    def _metric(
        self,
        name: str,
        value: float = 1.0,
    ) -> None:
        if self.metrics is not None:
            self.metrics.increment(
                name,
                value,
            )
