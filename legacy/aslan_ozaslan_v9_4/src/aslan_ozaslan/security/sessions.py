from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import secrets

@dataclass(frozen=True)
class SessionRecord:
    token_hash: str
    user_id: str
    role: str
    created_at: datetime
    expires_at: datetime
    revoked: bool = False

class SessionManager:
    def __init__(self, ttl_minutes: int = 60):
        if ttl_minutes <= 0:
            raise ValueError("ttl_minutes pozitif olmalıdır")
        self.ttl_minutes = ttl_minutes
        self._sessions: dict[str, SessionRecord] = {}

    def create(self, user_id: str, role: str) -> str:
        token = secrets.token_urlsafe(32)
        token_hash = self._hash(token)
        now = datetime.now(timezone.utc)
        self._sessions[token_hash] = SessionRecord(
            token_hash=token_hash,
            user_id=user_id,
            role=role,
            created_at=now,
            expires_at=now + timedelta(minutes=self.ttl_minutes),
        )
        return token

    def validate(self, token: str) -> SessionRecord | None:
        token_hash = self._hash(token)
        record = self._sessions.get(token_hash)
        if record is None or record.revoked:
            return None
        if datetime.now(timezone.utc) >= record.expires_at:
            return None
        return record

    def revoke(self, token: str) -> None:
        token_hash = self._hash(token)
        record = self._sessions.get(token_hash)
        if record:
            self._sessions[token_hash] = SessionRecord(
                token_hash=record.token_hash,
                user_id=record.user_id,
                role=record.role,
                created_at=record.created_at,
                expires_at=record.expires_at,
                revoked=True,
            )

    def _hash(self, token: str) -> str:
        return hashlib.sha256(token.encode("utf-8")).hexdigest()
