from __future__ import annotations
from datetime import datetime, timedelta, timezone

class OutboxLeaseManager:
    def __init__(self, outbox):
        self.outbox = outbox

    def claim(
        self,
        *,
        worker_id: str,
        limit: int = 50,
        lease_seconds: int = 30,
        now: datetime | None = None,
    ):
        if not worker_id.strip():
            raise ValueError("worker_id boş olamaz")
        if limit <= 0 or lease_seconds <= 0:
            raise ValueError("limit ve lease_seconds pozitif olmalıdır")

        current = now or datetime.now(timezone.utc)
        current_iso = current.isoformat()
        lease_until = (current + timedelta(seconds=lease_seconds)).isoformat()

        with self.outbox._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = connection.execute(
                '''
                SELECT message_id
                FROM outbox_messages
                WHERE status IN ('PENDING', 'RETRY')
                  AND available_at <= ?
                  AND (
                    lease_until IS NULL
                    OR lease_until < ?
                  )
                ORDER BY available_at, created_at
                LIMIT ?
                ''',
                (current_iso, current_iso, limit),
            ).fetchall()

            ids = [row["message_id"] for row in rows]
            for message_id in ids:
                connection.execute(
                    '''
                    UPDATE outbox_messages
                    SET status='PROCESSING',
                        lease_owner=?,
                        lease_until=?,
                        updated_at=?
                    WHERE message_id=?
                    ''',
                    (worker_id, lease_until, current_iso, message_id),
                )

            claimed = []
            for message_id in ids:
                row = connection.execute(
                    '''
                    SELECT * FROM outbox_messages
                    WHERE message_id=?
                    ''',
                    (message_id,),
                ).fetchone()
                claimed.append(self.outbox._row_to_message(row))

        return tuple(claimed)

    def release_expired(self, *, now: datetime | None = None) -> int:
        current_iso = (now or datetime.now(timezone.utc)).isoformat()
        with self.outbox._connect() as connection:
            cursor = connection.execute(
                '''
                UPDATE outbox_messages
                SET status='RETRY',
                    lease_owner=NULL,
                    lease_until=NULL,
                    updated_at=?
                WHERE status='PROCESSING'
                  AND lease_until < ?
                ''',
                (current_iso, current_iso),
            )
            return cursor.rowcount
