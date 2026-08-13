from dataclasses import dataclass
import json
from aslan_ozaslan.database import ProductionDatabase

@dataclass(frozen=True)
class PredictionRecord:
    calculation_id: str
    fixture_id: str
    model_version: str
    status: str
    home_probability: float | None
    draw_probability: float | None
    away_probability: float | None
    home_expected_goals: float | None
    away_expected_goals: float | None
    data_confidence: int
    warnings: tuple[str, ...]
    created_at: str | None = None

class PredictionRepository:
    def __init__(self, database: ProductionDatabase):
        self.database = database

    def insert(self, record: PredictionRecord) -> None:
        if record.status == "OK":
            probs = (record.home_probability, record.draw_probability, record.away_probability)
            if any(v is None for v in probs):
                raise ValueError("OK tahminde olasılıklar zorunludur")
            if abs(sum(probs) - 1.0) > 1e-6:
                raise ValueError("Olasılıkların toplamı 1 olmalıdır")
        with self.database.connect() as connection:
            connection.execute(
                '''
                INSERT INTO predictions(
                    calculation_id, fixture_id, model_version, status,
                    home_probability, draw_probability, away_probability,
                    home_expected_goals, away_expected_goals,
                    data_confidence, warnings_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''',
                (
                    record.calculation_id, record.fixture_id, record.model_version,
                    record.status, record.home_probability, record.draw_probability,
                    record.away_probability, record.home_expected_goals,
                    record.away_expected_goals, record.data_confidence,
                    json.dumps(record.warnings, ensure_ascii=False),
                ),
            )

    def latest_for_fixture(self, fixture_id: str):
        with self.database.connect() as connection:
            row = connection.execute(
                '''
                SELECT calculation_id, fixture_id, model_version, status,
                       home_probability, draw_probability, away_probability,
                       home_expected_goals, away_expected_goals,
                       data_confidence, warnings_json, created_at
                FROM predictions
                WHERE fixture_id = ?
                ORDER BY created_at DESC, rowid DESC
                LIMIT 1
                ''',
                (fixture_id,),
            ).fetchone()
        if row is None:
            return None
        return PredictionRecord(
            row["calculation_id"], row["fixture_id"], row["model_version"],
            row["status"], row["home_probability"], row["draw_probability"],
            row["away_probability"], row["home_expected_goals"],
            row["away_expected_goals"], row["data_confidence"],
            tuple(json.loads(row["warnings_json"])), row["created_at"]
        )
