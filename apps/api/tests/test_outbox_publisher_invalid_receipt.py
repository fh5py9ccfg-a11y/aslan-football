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

    def schedule_retry(self, record, error, next_attempt_at):
        record.status = "RETRY_SCHEDULED"
        record.error = error
        record.next_attempt_at = next_attempt_at
        return record

    def mark_dead_letter(self, record, error):
        record.status = "DEAD_LETTER"
        return record

class Transport:
    def publish(self, *, event_id, payload):
        return PublishReceipt(
            event_id="wrong",
            transport="test",
            destination="memory",
            accepted=True,
            external_id="x1",
            payload_sha256="c" * 64,
            published_at=100,
        )

def test_mismatched_receipt_schedules_retry():
    publisher = CompensationOutboxPublisher(
        committer=None,
        delivery_repository=Repo(),
        transport=Transport(),
        base_backoff_seconds=10,
    )

    result = publisher.publish_event(
        Event(),
        now=100,
    )

    assert result.status == "RETRY_SCHEDULED"
    assert result.next_attempt_at == 110
