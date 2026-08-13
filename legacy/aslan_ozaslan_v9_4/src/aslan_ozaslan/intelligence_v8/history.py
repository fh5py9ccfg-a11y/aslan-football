from __future__ import annotations
import json
from pathlib import Path

class RecommendationHistoryRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, fixture_id: str, opinions, recommendation) -> None:
        data = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))

        data.append({
            "fixture_id": fixture_id,
            "recommendation": {
                "action": recommendation.action,
                "confidence": recommendation.confidence,
                "risk": recommendation.risk,
                "urgency": recommendation.urgency,
                "approved": recommendation.approved,
                "rationale": list(recommendation.rationale),
            },
            "opinions": [
                {
                    "agent_name": opinion.agent_name,
                    "recommendation": opinion.recommendation,
                    "confidence": opinion.confidence,
                    "risk": opinion.risk,
                    "rationale": opinion.rationale,
                }
                for opinion in opinions
            ],
        })

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)
