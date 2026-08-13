from __future__ import annotations
import asyncio
import json
from datetime import datetime, timedelta, timezone
from sqlalchemy import text

from .db import SessionLocal

class ConsolePublisher:
    async def publish(self, topic: str, payload: dict, message_id: str) -> None:
        print(json.dumps(
            {"topic": topic, "message_id": message_id, "payload": payload},
            ensure_ascii=False,
        ))

class PostgresOutboxWorker:
    def __init__(
        self,
        *,
        worker_id: str,
        publisher=None,
        max_attempts: int = 5,
    ):
        self.worker_id = worker_id
        self.publisher = publisher or ConsolePublisher()
        self.max_attempts = max_attempts

    def claim(self, limit: int = 50) -> list[dict]:
        session = SessionLocal()
        try:
            rows = session.execute(
                text(
                    '''
                    SELECT message_id, aggregate_id, topic, payload_json,
                           attempt_count
                    FROM outbox_messages
                    WHERE status IN ('PENDING', 'RETRY')
                      AND available_at <= NOW()
                    ORDER BY created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT :limit
                    '''
                ),
                {"limit": limit},
            ).mappings().all()

            ids = [row["message_id"] for row in rows]
            if ids:
                session.execute(
                    text(
                        '''
                        UPDATE outbox_messages
                        SET status='PROCESSING'
                        WHERE message_id = ANY(:ids)
                        '''
                    ),
                    {"ids": ids},
                )
                session.commit()
            return [dict(row) for row in rows]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def run_once(self, limit: int = 50) -> dict:
        rows = self.claim(limit=limit)
        published = retried = dead = 0

        for row in rows:
            try:
                await self.publisher.publish(
                    row["topic"],
                    json.loads(row["payload_json"]),
                    row["message_id"],
                )
                self._mark_published(row["message_id"])
                published += 1
            except Exception as exc:
                next_attempt = int(row["attempt_count"]) + 1
                if next_attempt >= self.max_attempts:
                    self._mark_dead(row["message_id"], str(exc))
                    dead += 1
                else:
                    self._mark_retry(
                        row["message_id"],
                        str(exc),
                        next_attempt,
                    )
                    retried += 1

        return {
            "claimed": len(rows),
            "published": published,
            "retried": retried,
            "dead_lettered": dead,
        }

    def _mark_published(self, message_id: str) -> None:
        with SessionLocal.begin() as session:
            session.execute(
                text(
                    '''
                    UPDATE outbox_messages
                    SET status='PUBLISHED', last_error=NULL
                    WHERE message_id=:message_id
                    '''
                ),
                {"message_id": message_id},
            )

    def _mark_retry(
        self,
        message_id: str,
        error: str,
        attempt_count: int,
    ) -> None:
        delay = min(300, 2 ** attempt_count)
        available_at = datetime.now(timezone.utc) + timedelta(seconds=delay)
        with SessionLocal.begin() as session:
            session.execute(
                text(
                    '''
                    UPDATE outbox_messages
                    SET status='RETRY',
                        attempt_count=:attempt_count,
                        last_error=:error,
                        available_at=:available_at
                    WHERE message_id=:message_id
                    '''
                ),
                {
                    "attempt_count": attempt_count,
                    "error": error,
                    "available_at": available_at,
                    "message_id": message_id,
                },
            )

    def _mark_dead(self, message_id: str, error: str) -> None:
        with SessionLocal.begin() as session:
            session.execute(
                text(
                    '''
                    UPDATE outbox_messages
                    SET status='DEAD_LETTER',
                        attempt_count=attempt_count+1,
                        last_error=:error
                    WHERE message_id=:message_id
                    '''
                ),
                {"error": error, "message_id": message_id},
            )
