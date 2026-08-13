from dataclasses import dataclass

@dataclass(frozen=True)
class ProviderSyncReport:
    fetched: int
    published: int
    failed: int

class SportmonksFixtureSyncService:
    def __init__(self, *, client, publisher):
        self.client = client
        self.publisher = publisher

    async def sync_between(
        self, *, start_date, end_date,
        include="participants;scores;state", max_pages=100,
    ):
        fetched = published = failed = 0
        async for fixture in self.client.iter_fixtures_between(
            start_date, end_date, include=include, max_pages=max_pages
        ):
            fetched += 1
            try:
                fixture_id = str(fixture["id"])
                await self.publisher.publish(
                    "provider.fixtures",
                    fixture,
                    f"sportmonks:fixture:{fixture_id}",
                )
                published += 1
            except Exception:
                failed += 1
        return ProviderSyncReport(fetched, published, failed)
