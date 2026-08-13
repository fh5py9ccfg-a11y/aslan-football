from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class PublishResult:
    success: bool
    error: str | None = None

class OutboxPublisher:
    def __init__(self, publish_callable):
        self.publish_callable = publish_callable

    def publish(self, message) -> PublishResult:
        try:
            self.publish_callable(
                topic=message.topic,
                payload=message.payload,
                message_id=message.message_id,
            )
            return PublishResult(True, None)
        except Exception as exc:
            return PublishResult(False, str(exc))
