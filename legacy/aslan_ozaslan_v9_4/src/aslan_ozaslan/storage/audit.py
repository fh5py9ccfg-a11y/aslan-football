from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json, sqlite3
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    fixture_id: str
    status: str
    model_version: str
    calculation_id: str
    created_at: str
    payload: dict[str, Any]

    @classmethod
    def create(cls, *, event_type, fixture_id, status, model_version, calculation_id, payload):
        return cls(
            event_type=event_type,
            fixture_id=fixture_id,
            status=status,
            model_version=model_version,
            calculation_id=calculation_id,
            created_at=datetime.now(timezone.utc).isoformat(),
            payload=payload,
        )

class SQLiteAuditRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self):
        return sqlite3.connect(self.database_path)

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    fixture_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    calculation_id TEXT NOT NULL UNIQUE,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def append(self, event: AuditEvent):
        values = asdict(event)
        payload_json = json.dumps(values.pop("payload"), ensure_ascii=False, sort_keys=True)
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO audit_events (
                    event_type, fixture_id, status, model_version,
                    calculation_id, created_at, payload_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    values["event_type"], values["fixture_id"], values["status"],
                    values["model_version"], values["calculation_id"],
                    values["created_at"], payload_json,
                ),
            )

    def list_for_fixture(self, fixture_id: str):
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT event_type, fixture_id, status, model_version,
                       calculation_id, created_at, payload_json
                FROM audit_events WHERE fixture_id = ? ORDER BY id ASC
                """,
                (fixture_id,),
            ).fetchall()
        return [
            AuditEvent(
                event_type=r[0], fixture_id=r[1], status=r[2], model_version=r[3],
                calculation_id=r[4], created_at=r[5], payload=json.loads(r[6])
            )
            for r in rows
        ]
