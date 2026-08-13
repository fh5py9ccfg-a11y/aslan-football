from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class StreamWorkerReport:
    read: int
    processed: int
    duplicates: int
    acknowledged: int
    failed: int

class RedisStreamWorker:
    def __init__(
        self,
        *,
        consumer,
        receipt_repository,
        handler,
        consumer_group: str,
    ):
        self.consumer = consumer
        self.receipts = receipt_repository
        self.handler = handler
        self.consumer_group = consumer_group

    async def run_once(
        self,
        *,
        stream: str,
        count: int = 10,
        block_ms: int = 1000,
    ) -> StreamWorkerReport:
        messages = self.consumer.read(
            stream=stream,
            count=count,
            block_ms=block_ms,
        )
        processed = duplicates = acknowledged = failed = 0

        for message in messages:
            claimed = self.receipts.claim(
                consumer_group=self.consumer_group,
                message_id=message.message_id,
            )
            if not claimed:
                duplicates += 1
                acknowledged += self.consumer.acknowledge(message)
                continue

            try:
                await self.handler(message)
                processed += 1
                acknowledged += self.consumer.acknowledge(message)
            except Exception:
                failed += 1

        return StreamWorkerReport(
            read=len(messages),
            processed=processed,
            duplicates=duplicates,
            acknowledged=acknowledged,
            failed=failed,
        )
