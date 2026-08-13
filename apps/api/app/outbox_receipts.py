from __future__ import annotations
import json

from .outbox_transport import PublishReceipt

class RedisPublishReceiptRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:compensation-outbox-receipt",
        ttl_seconds: int = 2_592_000,
    ):
        if ttl_seconds <= 0:
            raise ValueError("receipt ttl pozitif olmalıdır")
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save(
        self,
        receipt: PublishReceipt,
    ) -> None:
        self.client.setex(
            self._key(receipt.event_id),
            self.ttl_seconds,
            json.dumps(
                receipt.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )

    def get(
        self,
        event_id: str,
    ) -> PublishReceipt | None:
        payload = self.client.get(
            self._key(event_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return PublishReceipt(
            **json.loads(payload)
        )

    def _key(
        self,
        event_id: str,
    ) -> str:
        return f"{self.prefix}:{event_id}"
