from __future__ import annotations

from datetime import datetime
import sqlite3
from pathlib import Path

from aslan_ozaslan.domain import FixtureRecord, TeamSnapshot


class SQLiteHistoryRepository:
    def __init__(self, database_path: str | Path):
        self.database_path = str(database_path)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.database_path)

    def _initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS fixtures (
                    provider TEXT NOT NULL,
                    fixture_id TEXT NOT NULL,
                    competition_id TEXT NOT NULL,
                    season TEXT NOT NULL,
                    kickoff_at TEXT NOT NULL,
                    home_team_id TEXT NOT NULL,
                    away_team_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    PRIMARY KEY (provider, fixture_id)
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS team_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    provider TEXT NOT NULL,
                    team_id TEXT NOT NULL,
                    competition_id TEXT NOT NULL,
                    observed_at TEXT NOT NULL,
                    matches_played INTEGER NOT NULL,
                    goals_for INTEGER NOT NULL,
                    goals_against INTEGER NOT NULL,
                    home_matches INTEGER NOT NULL,
                    away_matches INTEGER NOT NULL,
                    injuries_known INTEGER NOT NULL,
                    lineup_known INTEGER NOT NULL,
                    UNIQUE(provider, team_id, competition_id, observed_at)
                )
                """
            )

    def upsert_fixture(self, fixture: FixtureRecord) -> None:
        if fixture.home_team_id == fixture.away_team_id:
            raise ValueError("Ev ve deplasman takımı aynı olamaz")
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO fixtures (
                    provider, fixture_id, competition_id, season, kickoff_at,
                    home_team_id, away_team_id, status, observed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(provider, fixture_id) DO UPDATE SET
                    competition_id = excluded.competition_id,
                    season = excluded.season,
                    kickoff_at = excluded.kickoff_at,
                    home_team_id = excluded.home_team_id,
                    away_team_id = excluded.away_team_id,
                    status = excluded.status,
                    observed_at = excluded.observed_at
                """,
                (
                    fixture.provider,
                    fixture.fixture_id,
                    fixture.competition_id,
                    fixture.season,
                    fixture.kickoff_at.isoformat(),
                    fixture.home_team_id,
                    fixture.away_team_id,
                    fixture.status,
                    fixture.observed_at.isoformat(),
                ),
            )

    def add_team_snapshot(self, snapshot: TeamSnapshot) -> None:
        numeric = [
            snapshot.matches_played,
            snapshot.goals_for,
            snapshot.goals_against,
            snapshot.home_matches,
            snapshot.away_matches,
        ]
        if any(value < 0 for value in numeric):
            raise ValueError("Takım istatistikleri negatif olamaz")
        if snapshot.home_matches + snapshot.away_matches > snapshot.matches_played:
            raise ValueError("İç/dış saha maç toplamı oynanan maç sayısını aşamaz")

        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO team_snapshots (
                    provider, team_id, competition_id, observed_at,
                    matches_played, goals_for, goals_against,
                    home_matches, away_matches, injuries_known, lineup_known
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.provider,
                    snapshot.team_id,
                    snapshot.competition_id,
                    snapshot.observed_at.isoformat(),
                    snapshot.matches_played,
                    snapshot.goals_for,
                    snapshot.goals_against,
                    snapshot.home_matches,
                    snapshot.away_matches,
                    int(snapshot.injuries_known),
                    int(snapshot.lineup_known),
                ),
            )

    def latest_team_snapshot(
        self, *, provider: str, team_id: str, competition_id: str
    ) -> TeamSnapshot:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT provider, team_id, competition_id, observed_at,
                       matches_played, goals_for, goals_against,
                       home_matches, away_matches, injuries_known, lineup_known
                FROM team_snapshots
                WHERE provider = ? AND team_id = ? AND competition_id = ?
                ORDER BY observed_at DESC
                LIMIT 1
                """,
                (provider, team_id, competition_id),
            ).fetchone()
        if not row:
            raise LookupError("Takım geçmişi bulunamadı")
        return TeamSnapshot(
            provider=row[0],
            team_id=row[1],
            competition_id=row[2],
            observed_at=datetime.fromisoformat(row[3]),
            matches_played=row[4],
            goals_for=row[5],
            goals_against=row[6],
            home_matches=row[7],
            away_matches=row[8],
            injuries_known=bool(row[9]),
            lineup_known=bool(row[10]),
        )
