from __future__ import annotations
import json
from pathlib import Path

class DecisionHistoryRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, report) -> None:
        data = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))

        snapshot = report.snapshot
        data.append({
            "fixture_id": snapshot.fixture_id,
            "minute": snapshot.minute,
            "recommended_outcome": snapshot.recommended_outcome,
            "confidence": snapshot.confidence,
            "risk_score": snapshot.risk_score,
            "opportunity_score": snapshot.opportunity_score,
            "latency_ms": report.latency_ms,
            "degraded": report.degraded,
            "signals": [
                {
                    "signal_type": signal.signal_type,
                    "side": signal.side,
                    "strength": signal.strength,
                    "urgency": signal.urgency,
                    "explanation": signal.explanation,
                }
                for signal in snapshot.signals
            ],
        })

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def list_for_fixture(self, fixture_id: str) -> tuple[dict, ...]:
        if not self.path.exists():
            return ()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return tuple(
            item for item in data
            if item["fixture_id"] == fixture_id
        )
