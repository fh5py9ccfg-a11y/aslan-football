from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from typing import Any


@dataclass(frozen=True)
class RawPayload:
    provider: str
    resource_type: str
    external_id: str
    fetched_at: str
    content_hash: str
    payload: dict[str, Any]

    @classmethod
    def create(
        cls,
        *,
        provider: str,
        resource_type: str,
        external_id: str,
        payload: dict[str, Any],
        fetched_at: datetime | None = None,
    ) -> "RawPayload":
        normalized = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        return cls(
            provider=provider,
            resource_type=resource_type,
            external_id=external_id,
            fetched_at=(fetched_at or datetime.now(timezone.utc)).isoformat(),
            content_hash=sha256(normalized.encode("utf-8")).hexdigest(),
            payload=payload,
        )


class SQLiteRawArchive:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS raw_payloads (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    content_hash TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    UNIQUE(provider, resource_type, external_id, content_hash)
                )
                '''
            )

    def append(self, record: RawPayload) -> bool:
        try:
            with self._connect() as connection:
                connection.execute(
                    '''
                    INSERT INTO raw_payloads (
                        provider, resource_type, external_id,
                        fetched_at, content_hash, payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ''',
                    (
                        record.provider,
                        record.resource_type,
                        record.external_id,
                        record.fetched_at,
                        record.content_hash,
                        json.dumps(record.payload, ensure_ascii=False, sort_keys=True),
                    ),
                )
            return True
        except sqlite3.IntegrityError:
            return False

    def history(self, provider: str, resource_type: str, external_id: str) -> list[RawPayload]:
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT provider, resource_type, external_id,
                       fetched_at, content_hash, payload_json
                FROM raw_payloads
                WHERE provider = ? AND resource_type = ? AND external_id = ?
                ORDER BY id ASC
                ''',
                (provider, resource_type, external_id),
            ).fetchall()

        return [
            RawPayload(
                provider=row[0],
                resource_type=row[1],
                external_id=row[2],
                fetched_at=row[3],
                content_hash=row[4],
                payload=json.loads(row[5]),
            )
            for row in rows
        ]
