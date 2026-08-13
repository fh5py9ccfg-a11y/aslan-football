from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import sqlite3
from pathlib import Path
from uuid import uuid4


@dataclass(frozen=True)
class PersistentJob:
    job_id: str
    name: str
    payload: dict
    status: str
    attempts: int
    max_attempts: int
    next_run_at: str
    locked_by: str | None
    error: str | None


class SQLiteJobQueue:
    VALID_STATUSES = {"PENDING", "RUNNING", "SUCCEEDED", "FAILED", "DEAD"}

    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.executescript(
                '''
                CREATE TABLE IF NOT EXISTS background_jobs (
                    job_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    max_attempts INTEGER NOT NULL,
                    next_run_at TEXT NOT NULL,
                    locked_by TEXT,
                    error TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE INDEX IF NOT EXISTS idx_background_jobs_ready
                ON background_jobs(status, next_run_at);
                '''
            )

    def enqueue(
        self,
        name: str,
        payload: dict,
        *,
        max_attempts: int = 3,
        next_run_at: str | None = None,
    ) -> PersistentJob:
        if not name.strip():
            raise ValueError("İş adı boş olamaz")
        if max_attempts <= 0:
            raise ValueError("max_attempts pozitif olmalıdır")

        job_id = str(uuid4())
        run_at = next_run_at or datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO background_jobs(
                    job_id, name, payload_json, status,
                    attempts, max_attempts, next_run_at
                ) VALUES (?, ?, ?, 'PENDING', 0, ?, ?)
                ''',
                (
                    job_id,
                    name,
                    json.dumps(payload, ensure_ascii=False, sort_keys=True),
                    max_attempts,
                    run_at,
                ),
            )
        return self.get(job_id)

    def claim_next(self, worker_id: str) -> PersistentJob | None:
        if not worker_id.strip():
            raise ValueError("worker_id boş olamaz")

        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                '''
                SELECT job_id
                FROM background_jobs
                WHERE status = 'PENDING'
                  AND next_run_at <= ?
                ORDER BY next_run_at ASC, created_at ASC
                LIMIT 1
                ''',
                (now,),
            ).fetchone()
            if row is None:
                connection.commit()
                return None

            connection.execute(
                '''
                UPDATE background_jobs
                SET status='RUNNING',
                    locked_by=?,
                    attempts=attempts+1,
                    updated_at=CURRENT_TIMESTAMP
                WHERE job_id=? AND status='PENDING'
                ''',
                (worker_id, row["job_id"]),
            )
            connection.commit()
        return self.get(row["job_id"])

    def mark_succeeded(self, job_id: str, worker_id: str) -> None:
        self._transition(job_id, worker_id, "SUCCEEDED", None)

    def mark_failed(self, job_id: str, worker_id: str, error: str) -> None:
        job = self.get(job_id)
        if job is None:
            raise KeyError(job_id)
        target = "DEAD" if job.attempts >= job.max_attempts else "PENDING"
        self._transition(job_id, worker_id, target, error)

    def _transition(self, job_id: str, worker_id: str, status: str, error: str | None) -> None:
        if status not in self.VALID_STATUSES:
            raise ValueError("Geçersiz durum")
        with self._connect() as connection:
            cursor = connection.execute(
                '''
                UPDATE background_jobs
                SET status=?, locked_by=NULL, error=?, updated_at=CURRENT_TIMESTAMP
                WHERE job_id=? AND locked_by=? AND status='RUNNING'
                ''',
                (status, error, job_id, worker_id),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("İş kilidi veya durumu uyuşmuyor")

    def get(self, job_id: str) -> PersistentJob | None:
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT job_id, name, payload_json, status, attempts,
                       max_attempts, next_run_at, locked_by, error
                FROM background_jobs
                WHERE job_id=?
                ''',
                (job_id,),
            ).fetchone()
        if row is None:
            return None
        return PersistentJob(
            job_id=row["job_id"],
            name=row["name"],
            payload=json.loads(row["payload_json"]),
            status=row["status"],
            attempts=row["attempts"],
            max_attempts=row["max_attempts"],
            next_run_at=row["next_run_at"],
            locked_by=row["locked_by"],
            error=row["error"],
        )
