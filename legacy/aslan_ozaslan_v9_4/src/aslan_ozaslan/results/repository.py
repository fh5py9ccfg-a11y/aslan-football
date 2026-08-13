from __future__ import annotations

from dataclasses import dataclass
from aslan_ozaslan.database import ProductionDatabase


@dataclass(frozen=True)
class StoredMatchResult:
    fixture_id: str
    home_goals: int
    away_goals: int
    source: str
    settled_at: str | None = None


@dataclass(frozen=True)
class StoredSettlement:
    calculation_id: str
    fixture_id: str
    predicted_outcome: int
    actual_outcome: int
    correct: bool
    confidence: int
    model_version: str
    competition_id: str
    settled_at: str | None = None


class ResultRepository:
    def __init__(self, database: ProductionDatabase):
        self.database = database
        self._initialize()

    def _initialize(self) -> None:
        with self.database.connect() as connection:
            connection.executescript(
                '''
                CREATE TABLE IF NOT EXISTS match_results (
                    fixture_id TEXT PRIMARY KEY,
                    home_goals INTEGER NOT NULL CHECK(home_goals >= 0),
                    away_goals INTEGER NOT NULL CHECK(away_goals >= 0),
                    source TEXT NOT NULL,
                    settled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(fixture_id) REFERENCES fixtures(fixture_id)
                );

                CREATE TABLE IF NOT EXISTS settled_predictions (
                    calculation_id TEXT PRIMARY KEY,
                    fixture_id TEXT NOT NULL,
                    predicted_outcome INTEGER NOT NULL CHECK(predicted_outcome IN (0,1,2)),
                    actual_outcome INTEGER NOT NULL CHECK(actual_outcome IN (0,1,2)),
                    correct INTEGER NOT NULL CHECK(correct IN (0,1)),
                    confidence INTEGER NOT NULL CHECK(confidence BETWEEN 0 AND 100),
                    model_version TEXT NOT NULL,
                    competition_id TEXT NOT NULL,
                    settled_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(calculation_id) REFERENCES predictions(calculation_id),
                    FOREIGN KEY(fixture_id) REFERENCES fixtures(fixture_id)
                );

                CREATE INDEX IF NOT EXISTS idx_settled_competition_time
                ON settled_predictions(competition_id, settled_at DESC);

                CREATE INDEX IF NOT EXISTS idx_settled_model_time
                ON settled_predictions(model_version, settled_at DESC);
                '''
            )

    def upsert_result(self, result: StoredMatchResult) -> None:
        with self.database.connect() as connection:
            connection.execute(
                '''
                INSERT INTO match_results(fixture_id, home_goals, away_goals, source)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(fixture_id) DO UPDATE SET
                    home_goals=excluded.home_goals,
                    away_goals=excluded.away_goals,
                    source=excluded.source,
                    settled_at=CURRENT_TIMESTAMP
                ''',
                (result.fixture_id, result.home_goals, result.away_goals, result.source),
            )

    def save_settlement(self, settlement: StoredSettlement) -> None:
        with self.database.connect() as connection:
            connection.execute(
                '''
                INSERT OR REPLACE INTO settled_predictions(
                    calculation_id, fixture_id, predicted_outcome, actual_outcome,
                    correct, confidence, model_version, competition_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    settlement.calculation_id,
                    settlement.fixture_id,
                    settlement.predicted_outcome,
                    settlement.actual_outcome,
                    int(settlement.correct),
                    settlement.confidence,
                    settlement.model_version,
                    settlement.competition_id,
                ),
            )

    def league_rows(self, competition_id: str, limit: int = 500) -> list[StoredSettlement]:
        with self.database.connect() as connection:
            rows = connection.execute(
                '''
                SELECT calculation_id, fixture_id, predicted_outcome, actual_outcome,
                       correct, confidence, model_version, competition_id, settled_at
                FROM settled_predictions
                WHERE competition_id = ?
                ORDER BY settled_at DESC, rowid DESC
                LIMIT ?
                ''',
                (competition_id, limit),
            ).fetchall()
        return [
            StoredSettlement(
                calculation_id=row["calculation_id"],
                fixture_id=row["fixture_id"],
                predicted_outcome=row["predicted_outcome"],
                actual_outcome=row["actual_outcome"],
                correct=bool(row["correct"]),
                confidence=row["confidence"],
                model_version=row["model_version"],
                competition_id=row["competition_id"],
                settled_at=row["settled_at"],
            )
            for row in rows
        ]
