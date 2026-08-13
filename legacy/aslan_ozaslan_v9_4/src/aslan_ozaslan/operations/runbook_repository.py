from __future__ import annotations

from dataclasses import dataclass
import json
import sqlite3
from pathlib import Path

from .runbook_history import RunbookExecution


class SQLiteRunbookExecutionRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS runbook_executions (
                    execution_id TEXT PRIMARY KEY,
                    incident_code TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_steps_json TEXT NOT NULL,
                    status TEXT NOT NULL
                )
                '''
            )

    def save(self, execution: RunbookExecution) -> None:
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO runbook_executions(
                    execution_id, incident_code, operator, started_at,
                    completed_steps_json, status
                ) VALUES (?, ?, ?, ?, ?, ?)
                ON CONFLICT(execution_id) DO UPDATE SET
                    completed_steps_json=excluded.completed_steps_json,
                    status=excluded.status
                ''',
                (
                    execution.execution_id,
                    execution.incident_code,
                    execution.operator,
                    execution.started_at,
                    json.dumps(execution.completed_steps, ensure_ascii=False),
                    execution.status,
                ),
            )

    def get(self, execution_id: str) -> RunbookExecution | None:
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT execution_id, incident_code, operator, started_at,
                       completed_steps_json, status
                FROM runbook_executions
                WHERE execution_id=?
                ''',
                (execution_id,),
            ).fetchone()
        if row is None:
            return None
        return RunbookExecution(
            execution_id=row["execution_id"],
            incident_code=row["incident_code"],
            operator=row["operator"],
            started_at=row["started_at"],
            completed_steps=tuple(json.loads(row["completed_steps_json"])),
            status=row["status"],
        )
