from __future__ import annotations
from sqlalchemy import text
from .db import SessionLocal

class PostgresMessageReceiptRepository:
    def initialize(self) -> None:
        with SessionLocal.begin() as session:
            session.execute(
                text(
                    '''
                    CREATE TABLE IF NOT EXISTS message_receipts (
                        consumer_group TEXT NOT NULL,
                        message_id TEXT NOT NULL,
                        processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        PRIMARY KEY(consumer_group, message_id)
                    )
                    '''
                )
            )

    def claim(
        self,
        *,
        consumer_group: str,
        message_id: str,
    ) -> bool:
        self.initialize()
        with SessionLocal.begin() as session:
            result = session.execute(
                text(
                    '''
                    INSERT INTO message_receipts(
                        consumer_group,
                        message_id
                    )
                    VALUES (:consumer_group, :message_id)
                    ON CONFLICT DO NOTHING
                    RETURNING message_id
                    '''
                ),
                {
                    "consumer_group": consumer_group,
                    "message_id": message_id,
                },
            ).first()
            return result is not None
