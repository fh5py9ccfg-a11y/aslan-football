from __future__ import annotations

import sqlite3


class DeadLetterRetryService:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def retry(self, job_id: str) -> bool:
        connection = sqlite3.connect(self.database_path)
        try:
            cursor = connection.execute(
                '''
                UPDATE background_jobs
                SET status='PENDING',
                    locked_by=NULL,
                    error=NULL,
                    updated_at=CURRENT_TIMESTAMP
                WHERE job_id=? AND status='DEAD'
                ''',
                (job_id,),
            )
            connection.commit()
            return cursor.rowcount == 1
        finally:
            connection.close()
