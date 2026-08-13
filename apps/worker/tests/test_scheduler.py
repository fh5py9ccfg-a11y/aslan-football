import asyncio
from worker_app.scheduler import ProviderScheduler

class FixtureReport:
    fetched = 3
    published = 3

class FakeFixtureSync:
    async def sync_between(self, **kwargs):
        return FixtureReport()

class FakeEventSync:
    def __init__(self):
        self.ids = []

    async def sync_fixture(self, fixture_id):
        self.ids.append(fixture_id)

def test_scheduler_run_once():
    event_sync = FakeEventSync()

    async def fixture_ids_provider():
        return ("10", "11")

    scheduler = ProviderScheduler(
        fixture_sync_service=FakeFixtureSync(),
        event_sync_service=event_sync,
        fixture_ids_provider=fixture_ids_provider,
    )
    report = asyncio.run(scheduler.run_once())

    assert report.fixture_sync_fetched == 3
    assert report.fixture_sync_published == 3
    assert report.event_sync_count == 2
    assert event_sync.ids == ["10", "11"]
