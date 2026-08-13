from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass(frozen=True)
class DeadLetterJob:
    job_id: str
    name: str
    attempts: int
    error: str | None


class DeadLetterRepository:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def list(self, limit: int = 100) -> list[DeadLetterJob]:
        if limit <= 0:
            raise ValueError("limit pozitif olmalıdır")
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        try:
            rows = connection.execute(
                '''
                SELECT job_id, name, attempts, error
                FROM background_jobs
                WHERE status='DEAD'
                ORDER BY updated_at DESC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        finally:
            connection.close()

        return [
            DeadLetterJob(
                job_id=row["job_id"],
                name=row["name"],
                attempts=row["attempts"],
                error=row["error"],
            )
            for row in rows
        ]
