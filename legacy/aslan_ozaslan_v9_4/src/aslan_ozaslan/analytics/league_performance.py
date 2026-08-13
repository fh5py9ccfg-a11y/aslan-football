from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LeaguePerformance:
    competition_id: str
    settled_predictions: int
    accuracy: float
    average_confidence: float

class LeaguePerformanceCalculator:
    def calculate(self, competition_id: str, settled_rows) -> LeaguePerformance:
        rows = list(settled_rows)
        if not competition_id.strip():
            raise ValueError("competition_id boş olamaz")
        if not rows:
            return LeaguePerformance(competition_id, 0, 0.0, 0.0)

        correct = sum(int(row.correct) for row in rows)
        average_confidence = sum(row.confidence for row in rows) / len(rows)
        return LeaguePerformance(
            competition_id=competition_id,
            settled_predictions=len(rows),
            accuracy=round(correct / len(rows), 4),
            average_confidence=round(average_confidence, 2),
        )
