from __future__ import annotations
import json
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from football_core import MatchEvent

from .db import SessionLocal
from .models import MatchEventModel, OutboxMessageModel

class PostgresEventRepository:
    def append(self, event: MatchEvent) -> bool:
        event.validate()
        session = SessionLocal()
        try:
            model = MatchEventModel(
                fixture_id=event.fixture_id,
                sequence=event.sequence,
                event_type=event.event_type,
                minute=event.minute,
                team=event.team,
            )
            outbox = OutboxMessageModel(
                message_id=f"match-event:{event.fixture_id}:{event.sequence}",
                aggregate_id=event.fixture_id,
                topic="match.events",
                payload_json=json.dumps(
                    {
                        "fixture_id": event.fixture_id,
                        "sequence": event.sequence,
                        "event_type": event.event_type,
                        "minute": event.minute,
                        "team": event.team,
                    },
                    ensure_ascii=False,
                ),
                status="PENDING",
            )
            session.add(model)
            session.add(outbox)
            session.commit()
            return True
        except IntegrityError:
            session.rollback()
            return False
        finally:
            session.close()

    def list(self, fixture_id: str) -> list[MatchEvent]:
        session = SessionLocal()
        try:
            rows = session.execute(
                select(MatchEventModel)
                .where(MatchEventModel.fixture_id == fixture_id)
                .order_by(MatchEventModel.sequence)
            ).scalars().all()
            return [
                MatchEvent(
                    fixture_id=row.fixture_id,
                    sequence=row.sequence,
                    event_type=row.event_type,
                    minute=row.minute,
                    team=row.team,
                )
                for row in rows
            ]
        finally:
            session.close()
