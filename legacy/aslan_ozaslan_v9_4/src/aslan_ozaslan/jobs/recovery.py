from __future__ import annotations

from datetime import datetime, timedelta, timezone
import sqlite3


class StaleJobRecovery:
    def __init__(self, database_path: str, lock_timeout_seconds: int = 300):
        if lock_timeout_seconds <= 0:
            raise ValueError("lock_timeout_seconds pozitif olmalıdır")
        self.database_path = database_path
        self.lock_timeout_seconds = lock_timeout_seconds

    def recover(self, now: datetime | None = None) -> int:
        moment = now or datetime.now(timezone.utc)
        cutoff = (moment - timedelta(seconds=self.lock_timeout_seconds)).isoformat()

        connection = sqlite3.connect(self.database_path)
        try:
            cursor = connection.execute(
                '''
                UPDATE background_jobs
                SET status='PENDING',
                    locked_by=NULL,
                    error='stale-lock-recovered',
                    updated_at=CURRENT_TIMESTAMP
                WHERE status='RUNNING'
                  AND updated_at <= ?
                  AND attempts < max_attempts
                ''',
                (cutoff,),
            )
            connection.commit()
            return cursor.rowcount
        finally:
            connection.close()
