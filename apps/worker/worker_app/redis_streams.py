from __future__ import annotations
import json
import os
from dataclasses import dataclass

@dataclass(frozen=True)
class RedisPublishResult:
    stream_id: str

class RedisStreamsPublisher:
    def __init__(self, client, *, maxlen: int = 100_000):
        self.client = client
        self.maxlen = maxlen

    async def publish(
        self,
        topic: str,
        payload: dict,
        message_id: str,
    ) -> RedisPublishResult:
        fields = {
            "message_id": message_id,
            "payload": json.dumps(payload, ensure_ascii=False),
        }
        stream_id = self.client.xadd(
            topic,
            fields,
            maxlen=self.maxlen,
            approximate=True,
        )
        if isinstance(stream_id, bytes):
            stream_id = stream_id.decode("utf-8")
        return RedisPublishResult(stream_id=str(stream_id))

def build_redis_client():
    from redis import Redis
    return Redis.from_url(
        os.getenv("REDIS_URL", "redis://redis:6379/0"),
        decode_responses=False,
    )
