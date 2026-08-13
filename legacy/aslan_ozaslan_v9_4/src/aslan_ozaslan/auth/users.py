from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from aslan_ozaslan.auth.passwords import PasswordHasher
from aslan_ozaslan.database import ProductionDatabase


@dataclass(frozen=True)
class UserRecord:
    user_id: str
    email: str
    role: str
    active: bool


class UserRepository:
    VALID_ROLES = {"OWNER", "ADMIN", "ANALYST", "VIEWER"}

    def __init__(self, database: ProductionDatabase, hasher: PasswordHasher | None = None):
        self.database = database
        self.hasher = hasher or PasswordHasher()

    def create(self, *, email: str, password: str, role: str) -> UserRecord:
        normalized_email = email.strip().lower()
        if "@" not in normalized_email:
            raise ValueError("Geçerli e-posta gerekli")
        if role not in self.VALID_ROLES:
            raise ValueError("Geçersiz rol")

        user_id = str(uuid4())
        password_hash = self.hasher.hash(password)

        with self.database.connect() as connection:
            connection.execute(
                '''
                INSERT INTO users(id, email, password_hash, role)
                VALUES (?, ?, ?, ?)
                ''',
                (user_id, normalized_email, password_hash, role),
            )

        return UserRecord(user_id, normalized_email, role, True)

    def authenticate(self, email: str, password: str) -> UserRecord | None:
        normalized_email = email.strip().lower()
        with self.database.connect() as connection:
            row = connection.execute(
                '''
                SELECT id, email, password_hash, role, active
                FROM users WHERE email = ?
                ''',
                (normalized_email,),
            ).fetchone()

        if row is None or not row["active"]:
            return None
        if not self.hasher.verify(password, row["password_hash"]):
            return None
        return UserRecord(row["id"], row["email"], row["role"], bool(row["active"]))
