from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4


@dataclass(frozen=True)
class ImmutableAuditRecord:
    audit_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    payload: dict
    created_at: str
    previous_hash: str
    record_hash: str


class AppendOnlyAuditRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS immutable_audit_records (
                    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    audit_id TEXT NOT NULL UNIQUE,
                    actor_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    previous_hash TEXT NOT NULL,
                    record_hash TEXT NOT NULL UNIQUE
                )
                '''
            )

    def append(
        self,
        *,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        payload: dict,
    ) -> ImmutableAuditRecord:
        if not all(
            value.strip()
            for value in (actor_id, action, resource_type, resource_id)
        ):
            raise ValueError("Audit alanları boş olamaz")

        created_at = datetime.now(timezone.utc).isoformat()
        audit_id = str(uuid4())
        payload_json = json.dumps(payload, ensure_ascii=False, sort_keys=True)

        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT record_hash
                FROM immutable_audit_records
                ORDER BY sequence_id DESC
                LIMIT 1
                '''
            ).fetchone()
            previous_hash = row["record_hash"] if row else "GENESIS"
            record_hash = self._hash_record(
                audit_id,
                actor_id,
                action,
                resource_type,
                resource_id,
                payload_json,
                created_at,
                previous_hash,
            )
            connection.execute(
                '''
                INSERT INTO immutable_audit_records(
                    audit_id, actor_id, action, resource_type, resource_id,
                    payload_json, created_at, previous_hash, record_hash
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    audit_id,
                    actor_id,
                    action,
                    resource_type,
                    resource_id,
                    payload_json,
                    created_at,
                    previous_hash,
                    record_hash,
                ),
            )

        return ImmutableAuditRecord(
            audit_id=audit_id,
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=dict(payload),
            created_at=created_at,
            previous_hash=previous_hash,
            record_hash=record_hash,
        )

    def verify_chain(self) -> bool:
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT audit_id, actor_id, action, resource_type, resource_id,
                       payload_json, created_at, previous_hash, record_hash
                FROM immutable_audit_records
                ORDER BY sequence_id ASC
                '''
            ).fetchall()

        expected_previous = "GENESIS"
        for row in rows:
            if row["previous_hash"] != expected_previous:
                return False
            expected_hash = self._hash_record(
                row["audit_id"],
                row["actor_id"],
                row["action"],
                row["resource_type"],
                row["resource_id"],
                row["payload_json"],
                row["created_at"],
                row["previous_hash"],
            )
            if expected_hash != row["record_hash"]:
                return False
            expected_previous = row["record_hash"]
        return True

    def _hash_record(
        self,
        audit_id: str,
        actor_id: str,
        action: str,
        resource_type: str,
        resource_id: str,
        payload_json: str,
        created_at: str,
        previous_hash: str,
    ) -> str:
        raw = "|".join(
            [
                audit_id,
                actor_id,
                action,
                resource_type,
                resource_id,
                payload_json,
                created_at,
                previous_hash,
            ]
        ).encode("utf-8")
        return hashlib.sha256(raw).hexdigest()
