from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets
import sqlite3
from pathlib import Path


@dataclass(frozen=True)
class PersistentSession:
    token_hash: str
    user_id: str
    role: str
    created_at: str
    expires_at: str
    revoked: bool


class SQLiteSessionStore:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self):
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self):
        with self._connect() as connection:
            connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    expires_at TEXT NOT NULL,
                    revoked INTEGER NOT NULL DEFAULT 0 CHECK(revoked IN (0,1))
                )
                '''
            )

    def create(self, user_id: str, role: str, ttl_minutes: int = 60) -> str:
        if ttl_minutes <= 0:
            raise ValueError("ttl_minutes pozitif olmalıdır")
        token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)
        expires = now + timedelta(minutes=ttl_minutes)
        with self._connect() as connection:
            connection.execute(
                '''
                INSERT INTO sessions(token_hash, user_id, role, created_at, expires_at, revoked)
                VALUES (?, ?, ?, ?, ?, 0)
                ''',
                (token_hash, user_id, role, now.isoformat(), expires.isoformat()),
            )
        return token

    def get(self, token: str) -> PersistentSession | None:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self._connect() as connection:
            row = connection.execute(
                '''
                SELECT token_hash, user_id, role, created_at, expires_at, revoked
                FROM sessions WHERE token_hash = ?
                ''',
                (token_hash,),
            ).fetchone()
        if row is None:
            return None
        session = PersistentSession(
            token_hash=row["token_hash"],
            user_id=row["user_id"],
            role=row["role"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            revoked=bool(row["revoked"]),
        )
        if session.revoked:
            return None
        if datetime.now(timezone.utc) >= datetime.fromisoformat(session.expires_at):
            return None
        return session

    def revoke(self, token: str) -> None:
        token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
        with self._connect() as connection:
            connection.execute(
                "UPDATE sessions SET revoked = 1 WHERE token_hash = ?",
                (token_hash,),
            )

    def delete_expired(self) -> int:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as connection:
            cursor = connection.execute(
                "DELETE FROM sessions WHERE expires_at <= ? OR revoked = 1",
                (now,),
            )
            return cursor.rowcount
