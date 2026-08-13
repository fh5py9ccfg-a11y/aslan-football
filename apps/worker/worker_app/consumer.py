from __future__ import annotations
import json
from dataclasses import dataclass

@dataclass(frozen=True)
class ConsumedMessage:
    stream: str
    stream_id: str
    message_id: str
    payload: dict

class RedisStreamConsumer:
    def __init__(
        self,
        client,
        *,
        group: str,
        consumer_name: str,
    ):
        self.client = client
        self.group = group
        self.consumer_name = consumer_name

    def ensure_group(self, stream: str) -> None:
        try:
            self.client.xgroup_create(
                name=stream,
                groupname=self.group,
                id="0-0",
                mkstream=True,
            )
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise

    def read(
        self,
        *,
        stream: str,
        count: int = 10,
        block_ms: int = 1000,
    ) -> tuple[ConsumedMessage, ...]:
        self.ensure_group(stream)
        response = self.client.xreadgroup(
            groupname=self.group,
            consumername=self.consumer_name,
            streams={stream: ">"},
            count=count,
            block=block_ms,
        )
        messages = []
        for stream_name, entries in response:
            if isinstance(stream_name, bytes):
                stream_name = stream_name.decode("utf-8")
            for stream_id, fields in entries:
                if isinstance(stream_id, bytes):
                    stream_id = stream_id.decode("utf-8")
                normalized = {
                    (
                        key.decode("utf-8")
                        if isinstance(key, bytes)
                        else str(key)
                    ): (
                        value.decode("utf-8")
                        if isinstance(value, bytes)
                        else value
                    )
                    for key, value in fields.items()
                }
                messages.append(
                    ConsumedMessage(
                        stream=str(stream_name),
                        stream_id=str(stream_id),
                        message_id=str(normalized["message_id"]),
                        payload=json.loads(normalized["payload"]),
                    )
                )
        return tuple(messages)

    def acknowledge(self, message: ConsumedMessage) -> int:
        return int(
            self.client.xack(
                message.stream,
                self.group,
                message.stream_id,
            )
        )
