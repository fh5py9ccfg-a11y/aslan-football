from __future__ import annotations
import asyncio
import os

from .outbox_worker import PostgresOutboxWorker
from .redis_streams import RedisStreamsPublisher, build_redis_client

async def run() -> None:
    interval = float(os.getenv("WORKER_INTERVAL_SECONDS", "2"))
    client = build_redis_client()
    publisher = RedisStreamsPublisher(client)
    worker = PostgresOutboxWorker(
        worker_id=os.getenv("WORKER_ID", "worker-1"),
        publisher=publisher,
    )

    while True:
        report = await worker.run_once()
        print(report)
        await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(run())
