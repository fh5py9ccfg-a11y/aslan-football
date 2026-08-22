from __future__ import annotations
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TR = ZoneInfo("Europe/Istanbul")

@dataclass(frozen=True)
class SchedulerRunReport:
    fixture_sync_fetched: int
    fixture_sync_published: int
    event_sync_count: int

class ProviderScheduler:
    def __init__(
        self,
        *,
        fixture_sync_service,
        event_sync_service,
        fixture_ids_provider,
    ):
        self.fixture_sync = fixture_sync_service
        self.event_sync = event_sync_service
        self.fixture_ids_provider = fixture_ids_provider

    async def run_once(self) -> SchedulerRunReport:
        today_tr = datetime.now(TR).date()
        fixture_report = await self.fixture_sync.sync_between(
            start_date=(today_tr - timedelta(days=1)).isoformat(),
            end_date=(today_tr + timedelta(days=1)).isoformat(),
            max_pages=250,
        )

        configured_ids = await self.fixture_ids_provider()
        fixture_ids = tuple(dict.fromkeys(
            [str(item) for item in configured_ids]
            + [str(item) for item in getattr(fixture_report, "fixture_ids", ())]
        ))

        event_sync_count = 0
        for fixture_id in fixture_ids:
            try:
                await self.event_sync.sync_fixture(fixture_id)
                event_sync_count += 1
            except Exception:
                continue

        return SchedulerRunReport(
            fixture_sync_fetched=fixture_report.fetched,
            fixture_sync_published=fixture_report.published,
            event_sync_count=event_sync_count,
        )

    async def run_forever(self, interval_seconds: float = 30.0):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds pozitif olmalıdır")
        while True:
            try:
                await self.run_once()
            except Exception:
                pass
            await asyncio.sleep(interval_seconds)
