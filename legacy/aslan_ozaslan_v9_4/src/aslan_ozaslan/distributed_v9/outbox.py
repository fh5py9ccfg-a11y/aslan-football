from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .domain import OutboxMessage

class SQLiteTransactionalOutbox:
    def __init__(self, path: str | Path):
        self.path = str(path)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS outbox_messages (
                    message_id TEXT PRIMARY KEY,
                    aggregate_id TEXT NOT NULL,
                    topic TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL DEFAULT 0,
                    available_at TEXT NOT NULL,
                    lease_owner TEXT,
                    lease_until TEXT,
                    last_error TEXT,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                '''
            )

    def enqueue(
        self,
        *,
        message_id: str,
        aggregate_id: str,
        topic: str,
        payload: dict,
        available_at: str | None = None,
    ) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        available = available_at or now
        try:
            with self._connect() as connection:
                connection.execute(
                    '''
                    INSERT INTO outbox_messages(
                        message_id, aggregate_id, topic, payload_json,
                        status, attempt_count, available_at,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, 'PENDING', 0, ?, ?, ?)
                    ''',
                    (
                        message_id,
                        aggregate_id,
                        topic,
                        json.dumps(payload, ensure_ascii=False),
                        available,
                        now,
                        now,
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def get(self, message_id: str) -> OutboxMessage | None:
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT * FROM outbox_messages WHERE message_id=?
                ''',
                (message_id,),
            ).fetchone()
        return self._row_to_message(row) if row else None

    def list_by_status(self, status: str) -> tuple[OutboxMessage, ...]:
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT * FROM outbox_messages
                WHERE status=?
                ORDER BY created_at, message_id
                ''',
                (status,),
            ).fetchall()
        return tuple(self._row_to_message(row) for row in rows)

    def _row_to_message(self, row) -> OutboxMessage:
        return OutboxMessage(
            message_id=row["message_id"],
            aggregate_id=row["aggregate_id"],
            topic=row["topic"],
            payload=json.loads(row["payload_json"]),
            status=row["status"],
            attempt_count=int(row["attempt_count"]),
            available_at=row["available_at"],
            lease_owner=row["lease_owner"],
            lease_until=row["lease_until"],
            last_error=row["last_error"],
        )
