from dataclasses import dataclass

from apps.api.app.compensation_outbox_publisher import (
    CompensationOutboxPublisher,
)
from apps.api.app.outbox_transport import PublishReceipt

@dataclass
class Event:
    event_id: str = "e1"

class Delivery:
    status = "IN_PROGRESS"
    attempts = 1

class Repo:
    def claim(self, **kwargs):
        return True, Delivery()

    def mark_delivered(self, record, now=None):
        record.status = "DELIVERED"
        return record

class Receipts:
    def __init__(self):
        self.items = []

    def save(self, receipt):
        self.items.append(receipt)

class Transport:
    def publish(self, *, event_id, payload):
        return PublishReceipt(
            event_id=event_id,
            transport="test",
            destination="memory",
            accepted=True,
            external_id="x1",
            payload_sha256="b" * 64,
            published_at=100,
        )

def test_publisher_persists_receipt_before_ack():
    receipts = Receipts()
    publisher = CompensationOutboxPublisher(
        committer=None,
        delivery_repository=Repo(),
        transport=Transport(),
        receipt_repository=receipts,
    )

    result = publisher.publish_event(
        Event(),
        now=100,
    )

    assert result.status == "DELIVERED"
    assert len(receipts.items) == 1
    assert receipts.items[0].external_id == "x1"
