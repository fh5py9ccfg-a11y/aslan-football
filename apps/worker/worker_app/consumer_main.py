from __future__ import annotations
import asyncio
import os

from .consumer import RedisStreamConsumer
from .idempotency import PostgresMessageReceiptRepository
from .provider_event_bridge import ProviderEventToApiBridge
from .redis_streams import build_redis_client
from .stream_worker import RedisStreamWorker

async def run():
    stream = os.getenv("EVENT_STREAM", "provider.events")
    group = os.getenv("EVENT_CONSUMER_GROUP", "api-bridge")
    consumer_name = os.getenv("EVENT_CONSUMER_NAME", "bridge-1")
    api_base_url = os.getenv("API_BASE_URL", "http://api:8000")

    redis_client = build_redis_client()
    consumer = RedisStreamConsumer(
        redis_client,
        group=group,
        consumer_name=consumer_name,
    )
    bridge = ProviderEventToApiBridge(
        api_base_url=api_base_url,
        provider_api_key_id=os.getenv("PROVIDER_API_KEY_ID"),
        provider_api_key=os.getenv("PROVIDER_API_KEY"),
    )
    receipts = PostgresMessageReceiptRepository()
    worker = RedisStreamWorker(
        consumer=consumer,
        receipt_repository=receipts,
        handler=bridge.handle,
        consumer_group=group,
    )

    try:
        while True:
            report = await worker.run_once(
                stream=stream,
                count=50,
                block_ms=2000,
            )
            print(report)
    finally:
        await bridge.close()

if __name__ == "__main__":
    asyncio.run(run())
