import asyncio
import json
from dataclasses import dataclass

from worker_app.redis_streams import RedisStreamsPublisher
from worker_app.consumer import RedisStreamConsumer
from worker_app.stream_worker import RedisStreamWorker

class FakeRedis:
    def __init__(self):
        self.streams = {}
        self.groups = set()
        self.acked = []

    def xadd(self, name, fields, maxlen=None, approximate=True):
        entries = self.streams.setdefault(name, [])
        stream_id = f"{len(entries)+1}-0"
        encoded = {
            key.encode(): (
                value.encode()
                if isinstance(value, str)
                else value
            )
            for key, value in fields.items()
        }
        entries.append((stream_id.encode(), encoded))
        return stream_id.encode()

    def xgroup_create(self, name, groupname, id="0-0", mkstream=True):
        key = (name, groupname)
        if key in self.groups:
            raise RuntimeError("BUSYGROUP Consumer Group name already exists")
        self.groups.add(key)
        self.streams.setdefault(name, [])

    def xreadgroup(
        self,
        groupname,
        consumername,
        streams,
        count,
        block,
    ):
        stream = next(iter(streams))
        entries = self.streams.get(stream, [])[:count]
        return [(stream.encode(), entries)]

    def xack(self, stream, group, stream_id):
        self.acked.append((stream, group, stream_id))
        return 1

class FakeReceipts:
    def __init__(self):
        self.items = set()

    def claim(self, *, consumer_group, message_id):
        key = (consumer_group, message_id)
        if key in self.items:
            return False
        self.items.add(key)
        return True

def test_publish_and_consume():
    redis = FakeRedis()
    publisher = RedisStreamsPublisher(redis)

    result = asyncio.run(
        publisher.publish(
            "match.events",
            {"fixture_id": "f1"},
            "msg-1",
        )
    )
    assert result.stream_id == "1-0"

    consumer = RedisStreamConsumer(
        redis,
        group="analytics",
        consumer_name="c1",
    )
    messages = consumer.read(stream="match.events")
    assert len(messages) == 1
    assert messages[0].message_id == "msg-1"
    assert messages[0].payload["fixture_id"] == "f1"

def test_stream_worker_idempotency():
    redis = FakeRedis()
    publisher = RedisStreamsPublisher(redis)
    asyncio.run(
        publisher.publish(
            "match.events",
            {"fixture_id": "f1"},
            "msg-1",
        )
    )

    consumer = RedisStreamConsumer(
        redis,
        group="analytics",
        consumer_name="c1",
    )
    receipts = FakeReceipts()
    handled = []

    async def handler(message):
        handled.append(message.message_id)

    worker = RedisStreamWorker(
        consumer=consumer,
        receipt_repository=receipts,
        handler=handler,
        consumer_group="analytics",
    )

    first = asyncio.run(
        worker.run_once(stream="match.events")
    )
    second = asyncio.run(
        worker.run_once(stream="match.events")
    )

    assert first.processed == 1
    assert second.duplicates == 1
    assert handled == ["msg-1"]
