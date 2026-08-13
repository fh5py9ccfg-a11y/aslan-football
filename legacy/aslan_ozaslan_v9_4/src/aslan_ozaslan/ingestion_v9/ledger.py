from __future__ import annotations
import sqlite3
from pathlib import Path

from .domain import IngestionRecord

class SQLiteIngestionLedger:
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
                CREATE TABLE IF NOT EXISTS ingestion_ledger (
                    provider TEXT NOT NULL,
                    payload_type TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    payload_hash TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempt_count INTEGER NOT NULL,
                    last_error TEXT,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    PRIMARY KEY(provider, payload_type, external_id, payload_hash)
                )
                '''
            )

    def get(
        self,
        *,
        provider: str,
        payload_type: str,
        external_id: str,
        payload_hash: str,
    ) -> IngestionRecord | None:
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT provider, payload_type, external_id, payload_hash,
                       status, attempt_count, last_error
                FROM ingestion_ledger
                WHERE provider=? AND payload_type=?
                  AND external_id=? AND payload_hash=?
                ''',
                (provider, payload_type, external_id, payload_hash),
            ).fetchone()

        if row is None:
            return None
        return IngestionRecord(
            provider=row["provider"],
            payload_type=row["payload_type"],
            external_id=row["external_id"],
            payload_hash=row["payload_hash"],
            status=row["status"],
            attempt_count=int(row["attempt_count"]),
            last_error=row["last_error"],
        )

    def mark(
        self,
        *,
        provider: str,
        payload_type: str,
        external_id: str,
        payload_hash: str,
        status: str,
        last_error: str | None = None,
    ) -> IngestionRecord:
        existing = self.get(
            provider=provider,
            payload_type=payload_type,
            external_id=external_id,
            payload_hash=payload_hash,
        )
        attempts = (existing.attempt_count if existing else 0) + 1

        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO ingestion_ledger(
                    provider, payload_type, external_id, payload_hash,
                    status, attempt_count, last_error
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, payload_type, external_id, payload_hash)
                DO UPDATE SET
                    status=excluded.status,
                    attempt_count=excluded.attempt_count,
                    last_error=excluded.last_error,
                    updated_at=CURRENT_TIMESTAMP
                ''',
                (
                    provider,
                    payload_type,
                    external_id,
                    payload_hash,
                    status,
                    attempts,
                    last_error,
                ),
            )

        return IngestionRecord(
            provider=provider,
            payload_type=payload_type,
            external_id=external_id,
            payload_hash=payload_hash,
            status=status,
            attempt_count=attempts,
            last_error=last_error,
        )

    def is_completed(
        self,
        *,
        provider: str,
        payload_type: str,
        external_id: str,
        payload_hash: str,
    ) -> bool:
        record = self.get(
            provider=provider,
            payload_type=payload_type,
            external_id=external_id,
            payload_hash=payload_hash,
        )
        return record is not None and record.status == "COMPLETED"
