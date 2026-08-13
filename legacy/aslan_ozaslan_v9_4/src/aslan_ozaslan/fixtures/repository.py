from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from aslan_ozaslan.database import ProductionDatabase


@dataclass(frozen=True)
class FixtureRecord:
    fixture_id: str
    competition_id: str
    season: str
    home_team_id: str
    away_team_id: str
    kickoff_at: str
    status: str


class FixtureRepository:
    def __init__(self, database: ProductionDatabase):
        self.database = database

    def upsert(self, fixture: FixtureRecord) -> None:
        if fixture.home_team_id == fixture.away_team_id:
            raise ValueError("Aynı takım iki tarafta olamaz")
        with self.database.connect() as connection:
            connection.execute(
                '''
                INSERT INTO fixtures(
                    fixture_id, competition_id, season,
                    home_team_id, away_team_id, kickoff_at, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(fixture_id) DO UPDATE SET
                    competition_id=excluded.competition_id,
                    season=excluded.season,
                    home_team_id=excluded.home_team_id,
                    away_team_id=excluded.away_team_id,
                    kickoff_at=excluded.kickoff_at,
                    status=excluded.status,
                    updated_at=CURRENT_TIMESTAMP
                ''',
                (
                    fixture.fixture_id,
                    fixture.competition_id,
                    fixture.season,
                    fixture.home_team_id,
                    fixture.away_team_id,
                    fixture.kickoff_at,
                    fixture.status,
                ),
            )

    def upcoming(self, limit: int = 50) -> list[FixtureRecord]:
        if limit <= 0:
            raise ValueError("limit pozitif olmalıdır")
        with self.database.connect() as connection:
            rows = connection.execute(
                '''
                SELECT fixture_id, competition_id, season,
                       home_team_id, away_team_id, kickoff_at, status
                FROM fixtures
                WHERE status IN ('SCHEDULED','TIMED')
                ORDER BY kickoff_at ASC
                LIMIT ?
                ''',
                (limit,),
            ).fetchall()
        return [
            FixtureRecord(
                fixture_id=row["fixture_id"],
                competition_id=row["competition_id"],
                season=row["season"],
                home_team_id=row["home_team_id"],
                away_team_id=row["away_team_id"],
                kickoff_at=row["kickoff_at"],
                status=row["status"],
            )
            for row in rows
        ]
