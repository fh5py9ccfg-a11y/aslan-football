import json, sqlite3
from pathlib import Path
from .domain import DomainEvent

class SQLiteEventStore:
    def __init__(self, path):
        self.path = str(path)
        with sqlite3.connect(self.path) as c:
            c.execute('''
            CREATE TABLE IF NOT EXISTS domain_events(
                fixture_id TEXT NOT NULL,
                sequence_id INTEGER NOT NULL,
                event_id TEXT NOT NULL UNIQUE,
                event_type TEXT NOT NULL,
                occurred_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                correlation_id TEXT,
                causation_id TEXT,
                metadata_json TEXT NOT NULL,
                PRIMARY KEY(fixture_id, sequence_id)
            )''')

    def append(self, event):
        event.validate()
        try:
            with sqlite3.connect(self.path) as c:
                c.execute('''
                INSERT INTO domain_events VALUES(?,?,?,?,?,?,?,?,?)
                ''', (
                    event.fixture_id, event.sequence, event.event_id,
                    event.event_type, event.occurred_at,
                    json.dumps(event.payload, ensure_ascii=False),
                    event.correlation_id, event.causation_id,
                    json.dumps(event.metadata or {}, ensure_ascii=False),
                ))
            return True
        except sqlite3.IntegrityError:
            return False

    def stream(self, fixture_id, after_sequence=-1, up_to_sequence=None):
        query = '''
        SELECT fixture_id,sequence_id,event_id,event_type,occurred_at,
               payload_json,correlation_id,causation_id,metadata_json
        FROM domain_events WHERE fixture_id=? AND sequence_id>?
        '''
        params = [fixture_id, after_sequence]
        if up_to_sequence is not None:
            query += " AND sequence_id<=?"
            params.append(up_to_sequence)
        query += " ORDER BY sequence_id"
        with sqlite3.connect(self.path) as c:
            c.row_factory = sqlite3.Row
            rows = c.execute(query, tuple(params)).fetchall()
        return tuple(DomainEvent(
            event_id=r["event_id"], fixture_id=r["fixture_id"],
            sequence=int(r["sequence_id"]), event_type=r["event_type"],
            occurred_at=r["occurred_at"], payload=json.loads(r["payload_json"]),
            correlation_id=r["correlation_id"], causation_id=r["causation_id"],
            metadata=json.loads(r["metadata_json"]),
        ) for r in rows)

    def last_sequence(self, fixture_id):
        with sqlite3.connect(self.path) as c:
            row = c.execute(
                "SELECT MAX(sequence_id) FROM domain_events WHERE fixture_id=?",
                (fixture_id,),
            ).fetchone()
        return int(row[0]) if row and row[0] is not None else -1
