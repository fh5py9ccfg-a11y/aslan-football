from dataclasses import dataclass

from apps.api.app.compensation_outbox_publisher import (
    CompensationOutboxPublisher,
)

@dataclass
class Event:
    event_id: str = "e1"

class Delivery:
    status = "IN_PROGRESS"
    attempts = 2

class Repo:
    def claim(self, **kwargs):
        return True, Delivery()

    def schedule_retry(self, record, error, next_attempt_at):
        record.status = "RETRY_SCHEDULED"
        record.next_attempt_at = next_attempt_at
        record.error = error
        return record

    def mark_dead_letter(self, record, error):
        record.status = "DEAD_LETTER"
        return record

class Transport:
    def publish(self, **kwargs):
        raise RuntimeError("broker unavailable")

def test_failure_schedules_exponential_retry():
    publisher = CompensationOutboxPublisher(
        committer=None,
        delivery_repository=Repo(),
        transport=Transport(),
        max_attempts=5,
        base_backoff_seconds=10,
    )

    result = publisher.publish_event(
        Event(),
        now=100,
    )

    assert result.status == "RETRY_SCHEDULED"
    assert result.next_attempt_at == 120
