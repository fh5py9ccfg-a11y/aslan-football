from dataclasses import dataclass

@dataclass(frozen=True)
class EventSyncReport:
    fixture_id: str
    fetched: int
    published: int
    skipped: int
    failed: int

class SportmonksEventSyncService:
    def __init__(self, *, client, publisher, checkpoints):
        self.client = client
        self.publisher = publisher
        self.checkpoints = checkpoints

    async def sync_fixture(self, fixture_id: str):
        key = f"fixture-events:{fixture_id}"
        checkpoint = self.checkpoints.load(key) or {}
        last_event_id = str(checkpoint.get("last_event_id", ""))

        page = 1
        fetched = published = skipped = failed = 0
        newest_event_id = last_event_id

        while True:
            result = await self.client.events_by_fixture(
                fixture_id,
                page=page,
            )
            for event in result.data:
                fetched += 1
                event_id = str(event["id"])
                if last_event_id and event_id <= last_event_id:
                    skipped += 1
                    continue
                try:
                    await self.publisher.publish(
                        "provider.events",
                        event,
                        f"sportmonks:event:{event_id}",
                    )
                    published += 1
                    if not newest_event_id or event_id > newest_event_id:
                        newest_event_id = event_id
                except Exception:
                    failed += 1

            if not result.has_more:
                break
            page += 1

        self.checkpoints.save(
            key,
            {
                "last_event_id": newest_event_id,
                "fetched": fetched,
                "published": published,
            },
        )
        return EventSyncReport(
            fixture_id=str(fixture_id),
            fetched=fetched,
            published=published,
            skipped=skipped,
            failed=failed,
        )
