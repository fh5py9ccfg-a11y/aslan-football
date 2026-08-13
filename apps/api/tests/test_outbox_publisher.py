from dataclasses import dataclass

from apps.api.app.compensation_outbox_publisher import (
    CompensationOutboxPublisher,
)

@dataclass
class Event:
    event_id: str = "e1"
    compensation_id: str = "c1"
    request_id: str = "r1"
    claim_id: str = "q1"
    action: str = "ACTION"
    status: str = "COMPLETED"
    payload: dict = None
    created_at: int = 1

class Committer:
    def list_events(self, limit):
        return (Event(payload={"ok": True}),)

class Delivery:
    status = "IN_PROGRESS"
    attempts = 1

class Repo:
    def claim(self, **kwargs):
        return True, Delivery()

    def mark_delivered(self, record, now=None):
        record.status = "DELIVERED"
        return record

    def schedule_retry(self, record, error, next_attempt_at):
        record.status = "RETRY_SCHEDULED"
        record.error = error
        record.next_attempt_at = next_attempt_at
        return record

    def mark_dead_letter(self, record, error):
        record.status = "DEAD_LETTER"
        return record

class Transport:
    def __init__(self):
        self.calls = 0

    def publish(self, *, event_id, payload):
        self.calls += 1

def test_publisher_delivers_event_once():
    transport = Transport()
    publisher = CompensationOutboxPublisher(
        committer=Committer(),
        delivery_repository=Repo(),
        transport=transport,
    )

    result = publisher.publish_batch(
        limit=10,
        now=100,
    )

    assert result[0].status == "DELIVERED"
    assert transport.calls == 1
