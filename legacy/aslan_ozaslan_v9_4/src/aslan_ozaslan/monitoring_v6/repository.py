from __future__ import annotations
import json
from pathlib import Path

class MonitoringHistoryRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, snapshot, drift, safe_mode) -> None:
        data = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))

        data.append({
            "samples": snapshot.samples,
            "average_confidence": snapshot.average_confidence,
            "average_risk": snapshot.average_risk,
            "p95_latency_ms": snapshot.p95_latency_ms,
            "degraded_ratio": snapshot.degraded_ratio,
            "drift_detected": snapshot.drift_detected,
            "circuit_open": snapshot.circuit_open,
            "safe_mode": snapshot.safe_mode,
            "drift_reasons": list(drift.reasons),
            "safe_mode_reason": safe_mode.reason,
        })

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)
