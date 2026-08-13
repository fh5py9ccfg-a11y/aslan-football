from apps.api.app.outbox_receipts import (
    RedisPublishReceiptRepository,
)
from apps.api.app.outbox_transport import PublishReceipt

class Redis:
    def __init__(self):
        self.values = {}

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

def test_receipt_save_and_load():
    repo = RedisPublishReceiptRepository(
        Redis(),
        prefix="receipt",
    )
    receipt = PublishReceipt(
        event_id="e1",
        transport="logging",
        destination="application-log",
        accepted=True,
        external_id="e1",
        payload_sha256="a" * 64,
        published_at=100,
    )

    repo.save(receipt)
    loaded = repo.get("e1")

    assert loaded == receipt
