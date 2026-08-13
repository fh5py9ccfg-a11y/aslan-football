from __future__ import annotations
import json
import sqlite3
from pathlib import Path

class DeadLetterReplayRepository:
    def __init__(self, path: str | Path):
        self.path = str(path)

    def list_items(self, limit: int = 100) -> list[dict]:
        with sqlite3.connect(self.path) as connection:
            connection.row_factory = sqlite3.Row
            rows = connection.execute(
                '''
                SELECT id, topic, partition_id, offset_id, key, payload, error
                FROM dead_letter
                ORDER BY id
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "topic": row["topic"],
                "partition": row["partition_id"],
                "offset": row["offset_id"],
                "key": row["key"],
                "value": json.loads(row["payload"]),
                "error": row["error"],
            }
            for row in rows
        ]

    def delete(self, item_id: int) -> None:
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                "DELETE FROM dead_letter WHERE id=?",
                (item_id,),
            )

class DeadLetterReplayer:
    def __init__(self, *, repository: DeadLetterReplayRepository, producer):
        self.repository = repository
        self.producer = producer

    def replay(
        self,
        limit: int = 100,
        target_topic_suffix: str = ".retry",
    ) -> int:
        count = 0
        for item in self.repository.list_items(limit=limit):
            self.producer.publish(
                topic=item["topic"] + target_topic_suffix,
                key=item["key"],
                value=item["value"],
                headers={
                    "x-original-topic": item["topic"],
                    "x-original-offset": str(item["offset"]),
                    "x-replay": "true",
                },
            )
            self.repository.delete(item["id"])
            count += 1
        return count
