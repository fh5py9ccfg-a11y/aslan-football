from dataclasses import dataclass

from apps.api.app.compensation_outbox_publisher import (
    CompensationOutboxPublisher,
)

@dataclass
class Event:
    event_id: str = "e1"

class Delivery:
    status = "IN_PROGRESS"
    attempts = 5

class Repo:
    def claim(self, **kwargs):
        return True, Delivery()

    def mark_dead_letter(self, record, error):
        record.status = "DEAD_LETTER"
        record.error = error
        return record

class Transport:
    def publish(self, **kwargs):
        raise RuntimeError("permanent failure")

def test_max_attempts_moves_delivery_to_dead_letter():
    publisher = CompensationOutboxPublisher(
        committer=None,
        delivery_repository=Repo(),
        transport=Transport(),
        max_attempts=5,
    )

    result = publisher.publish_event(
        Event(),
        now=100,
    )

    assert result.status == "DEAD_LETTER"
