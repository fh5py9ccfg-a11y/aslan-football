from __future__ import annotations

from dataclasses import dataclass
import sqlite3
from pathlib import Path


@dataclass(frozen=True)
class IdentityConflict:
    provider: str
    external_team_id: str
    existing_canonical_id: str
    requested_canonical_id: str


class TeamIdentityRegistry:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS team_identity_map (
                    provider TEXT NOT NULL,
                    external_team_id TEXT NOT NULL,
                    canonical_team_id TEXT NOT NULL,
                    display_name TEXT NOT NULL,
                    PRIMARY KEY (provider, external_team_id)
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_team_identity_canonical
                ON team_identity_map(canonical_team_id)
                """
            )

    def register(
        self,
        *,
        provider: str,
        external_team_id: str,
        canonical_team_id: str,
        display_name: str,
    ) -> None:
        values = [provider, external_team_id, canonical_team_id, display_name]
        if any(not str(value).strip() for value in values):
            raise ValueError("Kimlik alanları boş bırakılamaz")

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT canonical_team_id
                FROM team_identity_map
                WHERE provider = ? AND external_team_id = ?
                """,
                (provider, external_team_id),
            ).fetchone()

            if row and row[0] != canonical_team_id:
                raise ValueError(
                    IdentityConflict(
                        provider=provider,
                        external_team_id=external_team_id,
                        existing_canonical_id=row[0],
                        requested_canonical_id=canonical_team_id,
                    )
                )

            connection.execute(
                """
                INSERT INTO team_identity_map (
                    provider, external_team_id, canonical_team_id, display_name
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(provider, external_team_id)
                DO UPDATE SET display_name = excluded.display_name
                """,
                (provider, external_team_id, canonical_team_id, display_name),
            )

    def resolve(self, provider: str, external_team_id: str) -> str:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT canonical_team_id
                FROM team_identity_map
                WHERE provider = ? AND external_team_id = ?
                """,
                (provider, external_team_id),
            ).fetchone()
        if not row:
            raise LookupError(f"Takım kimliği eşleşmedi: {provider}/{external_team_id}")
        return str(row[0])
