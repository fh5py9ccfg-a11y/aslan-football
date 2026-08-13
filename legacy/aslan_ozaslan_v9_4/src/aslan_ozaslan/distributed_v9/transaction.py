from __future__ import annotations
import json
from datetime import datetime, timezone

class IngestionOutboxTransaction:
    def __init__(self, outbox):
        self.outbox = outbox

    def archive_and_enqueue(
        self,
        *,
        archive_table: str,
        provider: str,
        payload_type: str,
        external_id: str,
        payload_hash: str,
        payload: dict,
        message_id: str,
        topic: str,
    ) -> bool:
        now = datetime.now(timezone.utc).isoformat()
        with self.outbox._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute(
                f'''
                CREATE TABLE IF NOT EXISTS {archive_table} (
                    provider TEXT NOT NULL,
                    payload_type TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    archived_at TEXT NOT NULL,
                    PRIMARY KEY(
                        provider, payload_type, external_id, payload_hash
                    )
                )
                '''
            )

            existing = connection.execute(
                f'''
                SELECT 1 FROM {archive_table}
                WHERE provider=? AND payload_type=?
                  AND external_id=? AND payload_hash=?
                ''',
                (provider, payload_type, external_id, payload_hash),
            ).fetchone()

            if existing:
                return False

            connection.execute(
                f'''
                INSERT INTO {archive_table}(
                    provider, payload_type, external_id,
                    payload_hash, payload_json, archived_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                ''',
                (
                    provider,
                    payload_type,
                    external_id,
                    payload_hash,
                    json.dumps(payload, ensure_ascii=False),
                    now,
                ),
            )

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
                    external_id,
                    topic,
                    json.dumps(payload, ensure_ascii=False),
                    now,
                    now,
                    now,
                ),
            )
        return True
