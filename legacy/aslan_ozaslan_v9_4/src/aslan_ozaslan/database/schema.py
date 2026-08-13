from __future__ import annotations

from pathlib import Path
import sqlite3


SCHEMA_VERSION = 1


class ProductionDatabase:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA journal_mode = WAL")
        return connection

    def _initialize(self) -> None:
        with self.connect() as connection:
            connection.executescript(
                '''
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('OWNER','ADMIN','ANALYST','VIEWER')),
                    active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS fixtures (
                    fixture_id TEXT PRIMARY KEY,
                    competition_id TEXT NOT NULL,
                    season TEXT NOT NULL,
                    home_team_id TEXT NOT NULL,
                    away_team_id TEXT NOT NULL,
                    kickoff_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CHECK(home_team_id <> away_team_id)
                );

                CREATE TABLE IF NOT EXISTS predictions (
                    calculation_id TEXT PRIMARY KEY,
                    fixture_id TEXT NOT NULL,
                    model_version TEXT NOT NULL,
                    status TEXT NOT NULL,
                    home_probability REAL,
                    draw_probability REAL,
                    away_probability REAL,
                    home_expected_goals REAL,
                    away_expected_goals REAL,
                    data_confidence INTEGER NOT NULL,
                    warnings_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(fixture_id) REFERENCES fixtures(fixture_id),
                    CHECK(data_confidence BETWEEN 0 AND 100),
                    CHECK(
                        status <> 'OK'
                        OR (
                            home_probability IS NOT NULL
                            AND draw_probability IS NOT NULL
                            AND away_probability IS NOT NULL
                            AND ABS(home_probability + draw_probability + away_probability - 1.0) < 0.00001
                        )
                    )
                );

                CREATE TABLE IF NOT EXISTS provider_runs (
                    run_id TEXT PRIMARY KEY,
                    provider_name TEXT NOT NULL,
                    resource_type TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    finished_at TEXT,
                    status TEXT NOT NULL,
                    records_received INTEGER NOT NULL DEFAULT 0,
                    error_code TEXT,
                    error_message TEXT
                );

                CREATE INDEX IF NOT EXISTS idx_fixtures_kickoff
                    ON fixtures(kickoff_at);

                CREATE INDEX IF NOT EXISTS idx_predictions_fixture_created
                    ON predictions(fixture_id, created_at DESC);

                INSERT OR IGNORE INTO schema_migrations(version) VALUES (1);
                '''
            )

    def schema_version(self) -> int:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT MAX(version) AS version FROM schema_migrations"
            ).fetchone()
            return int(row["version"] or 0)
