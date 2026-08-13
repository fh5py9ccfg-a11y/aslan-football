from dataclasses import dataclass
from datetime import datetime, timezone
import json
from threading import Lock

@dataclass(frozen=True)
class AuditEvent:
    action: str
    subject: str
    resource: str
    outcome: str
    correlation_id: str
    metadata: dict
    created_at: str

class InMemoryAuditRepository:
    def __init__(self):
        self._items = []
        self._lock = Lock()

    def append(self, event):
        with self._lock:
            self._items.append(event)

    def list(
        self,
        *,
        limit=100,
        offset=0,
        subject=None,
        resource=None,
        outcome=None,
    ):
        with self._lock:
            items = list(self._items)
        items = [
            item for item in items
            if (subject is None or item.subject == subject)
            and (resource is None or item.resource == resource)
            and (outcome is None or item.outcome == outcome)
        ]
        return tuple(
            items[offset:offset + limit]
        )

class JsonAuditRepository:
    def __init__(self, path):
        from pathlib import Path
        self.path = Path(path)
        self._lock = Lock()

    def append(self, event):
        with self._lock:
            data = []
            if self.path.exists():
                data = json.loads(
                    self.path.read_text(encoding="utf-8")
                )
            data.append(event.__dict__)
            self.path.parent.mkdir(
                parents=True,
                exist_ok=True,
            )
            temp = self.path.with_suffix(
                self.path.suffix + ".tmp"
            )
            temp.write_text(
                json.dumps(
                    data,
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            temp.replace(self.path)

    def list(
        self,
        *,
        limit=100,
        offset=0,
        subject=None,
        resource=None,
        outcome=None,
    ):
        if not self.path.exists():
            return ()
        items = [
            AuditEvent(**item)
            for item in json.loads(
                self.path.read_text(encoding="utf-8")
            )
        ]
        items = [
            item for item in items
            if (subject is None or item.subject == subject)
            and (resource is None or item.resource == resource)
            and (outcome is None or item.outcome == outcome)
        ]
        return tuple(items[offset:offset + limit])

class PostgresAuditRepository:
    def __init__(self, session_factory):
        self.session_factory = session_factory

    def append(self, event):
        from sqlalchemy import text
        with self.session_factory.begin() as session:
            session.execute(
                text(
                    '''
                    INSERT INTO audit_events(
                        action,
                        subject,
                        resource,
                        outcome,
                        correlation_id,
                        metadata_json,
                        created_at
                    )
                    VALUES (
                        :action,
                        :subject,
                        :resource,
                        :outcome,
                        :correlation_id,
                        :metadata_json,
                        :created_at
                    )
                    '''
                ),
                {
                    "action": event.action,
                    "subject": event.subject,
                    "resource": event.resource,
                    "outcome": event.outcome,
                    "correlation_id": event.correlation_id,
                    "metadata_json": json.dumps(
                        event.metadata,
                        ensure_ascii=False,
                    ),
                    "created_at": event.created_at,
                },
            )

    def list(
        self,
        *,
        limit=100,
        offset=0,
        subject=None,
        resource=None,
        outcome=None,
    ):
        from sqlalchemy import text
        clauses = []
        params = {
            "limit": limit,
            "offset": offset,
        }
        if subject is not None:
            clauses.append("subject = :subject")
            params["subject"] = subject
        if resource is not None:
            clauses.append("resource = :resource")
            params["resource"] = resource
        if outcome is not None:
            clauses.append("outcome = :outcome")
            params["outcome"] = outcome

        where_sql = (
            "WHERE " + " AND ".join(clauses)
            if clauses
            else ""
        )
        query = text(
            f'''
            SELECT action, subject, resource, outcome,
                   correlation_id, metadata_json, created_at
            FROM audit_events
            {where_sql}
            ORDER BY created_at DESC
            LIMIT :limit OFFSET :offset
            '''
        )

        with self.session_factory.begin() as session:
            rows = session.execute(
                query,
                params,
            ).mappings().all()

        return tuple(
            AuditEvent(
                action=row["action"],
                subject=row["subject"],
                resource=row["resource"],
                outcome=row["outcome"],
                correlation_id=row["correlation_id"],
                metadata=json.loads(
                    row["metadata_json"]
                ),
                created_at=(
                    row["created_at"].isoformat()
                    if hasattr(
                        row["created_at"],
                        "isoformat",
                    )
                    else str(row["created_at"])
                ),
            )
            for row in rows
        )

def make_audit_event(
    *,
    action,
    subject,
    resource,
    outcome,
    correlation_id,
    metadata=None,
):
    return AuditEvent(
        action=action,
        subject=subject,
        resource=resource,
        outcome=outcome,
        correlation_id=correlation_id,
        metadata=dict(metadata or {}),
        created_at=datetime.now(
            timezone.utc
        ).isoformat(),
    )
