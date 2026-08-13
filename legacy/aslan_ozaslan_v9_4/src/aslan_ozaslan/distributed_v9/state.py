from __future__ import annotations
from datetime import datetime, timezone

class OutboxStateRepository:
    def __init__(self, outbox):
        self.outbox = outbox

    def mark_published(self, message_id: str) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.outbox._connect() as connection:
            connection.execute(
                '''
                UPDATE outbox_messages
                SET status='PUBLISHED',
                    lease_owner=NULL,
                    lease_until=NULL,
                    last_error=NULL,
                    updated_at=?
                WHERE message_id=?
                ''',
                (now, message_id),
            )

    def mark_retry(
        self,
        *,
        message_id: str,
        error: str,
        available_at: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.outbox._connect() as connection:
            connection.execute(
                '''
                UPDATE outbox_messages
                SET status='RETRY',
                    attempt_count=attempt_count+1,
                    available_at=?,
                    lease_owner=NULL,
                    lease_until=NULL,
                    last_error=?,
                    updated_at=?
                WHERE message_id=?
                ''',
                (available_at, error, now, message_id),
            )

    def mark_dead_letter(
        self,
        *,
        message_id: str,
        error: str,
    ) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self.outbox._connect() as connection:
            connection.execute(
                '''
                UPDATE outbox_messages
                SET status='DEAD_LETTER',
                    attempt_count=attempt_count+1,
                    lease_owner=NULL,
                    lease_until=NULL,
                    last_error=?,
                    updated_at=?
                WHERE message_id=?
                ''',
                (error, now, message_id),
            )
