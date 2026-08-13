from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class AuditRecord:
    audit_id: str
    actor_id: str
    action: str
    resource_type: str
    resource_id: str
    payload: dict
    created_at: str


class AuditRepository:
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
                CREATE TABLE IF NOT EXISTS audit_records (
                    audit_id TEXT PRIMARY KEY,
                    actor_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    resource_id TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
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
    ) -> AuditRecord:
        if not all(
            value.strip()
            for value in (actor_id, action, resource_type, resource_id)
        ):
            raise ValueError("Audit alanları boş olamaz")

        record = AuditRecord(
            audit_id=str(uuid4()),
            actor_id=actor_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=dict(payload),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO audit_records(
                    audit_id, actor_id, action, resource_type,
                    resource_id, payload_json, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    record.audit_id,
                    record.actor_id,
                    record.action,
                    record.resource_type,
                    record.resource_id,
                    json.dumps(record.payload, ensure_ascii=False, sort_keys=True),
                    record.created_at,
                ),
            )
        return record

    def list_recent(self, limit: int = 100) -> list[AuditRecord]:
        if limit <= 0:
            raise ValueError("limit pozitif olmalıdır")
        with self._connect() as connection:
            rows = connection.execute(
                '''
                SELECT audit_id, actor_id, action, resource_type,
                       resource_id, payload_json, created_at
                FROM audit_records
                ORDER BY created_at DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()

        return [
            AuditRecord(
                audit_id=row["audit_id"],
                actor_id=row["actor_id"],
                action=row["action"],
                resource_type=row["resource_type"],
                resource_id=row["resource_id"],
                payload=json.loads(row["payload_json"]),
                created_at=row["created_at"],
            )
            for row in rows
        ]
