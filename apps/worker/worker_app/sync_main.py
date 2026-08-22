from __future__ import annotations
import asyncio
import os
from pathlib import Path

from .checkpoint import JsonCheckpointRepository
from .event_sync import SportmonksEventSyncService
from .provider_sync import SportmonksFixtureSyncService
from .redis_streams import RedisStreamsPublisher, build_redis_client
from .scheduler import ProviderScheduler
from .sportmonks import SportmonksClient


async def run():
    token = os.environ["SPORTMONKS_API_TOKEN"]
    interval = float(os.getenv("SPORTMONKS_SYNC_INTERVAL_SECONDS", "30"))
    predictions_enabled = os.getenv(
        "SPORTMONKS_PREDICTIONS_ENABLED", "true"
    ).strip().lower() in {"1", "true", "yes", "on"}
    fixture_ids_raw = os.getenv("SPORTMONKS_FIXTURE_IDS", "")
    fixture_ids = tuple(
        item.strip()
        for item in fixture_ids_raw.split(",")
        if item.strip()
    )

    redis_client = build_redis_client()
    publisher = RedisStreamsPublisher(redis_client)
    client = SportmonksClient(api_token=token)
    checkpoints = JsonCheckpointRepository(
        Path(os.getenv("CHECKPOINT_PATH", "/data/checkpoints.json"))
    )

    fixture_sync = SportmonksFixtureSyncService(
        client=client,
        publisher=publisher,
        predictions_enabled=predictions_enabled,
    )
    event_sync = SportmonksEventSyncService(
        client=client,
        publisher=publisher,
        checkpoints=checkpoints,
    )

    async def fixture_ids_provider():
        return fixture_ids

    scheduler = ProviderScheduler(
        fixture_sync_service=fixture_sync,
        event_sync_service=event_sync,
        fixture_ids_provider=fixture_ids_provider,
    )

    try:
        await scheduler.run_forever(interval_seconds=interval)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run())
