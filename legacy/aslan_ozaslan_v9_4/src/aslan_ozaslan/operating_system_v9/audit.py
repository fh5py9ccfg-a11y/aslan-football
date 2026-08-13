from __future__ import annotations
import json
from pathlib import Path

class DecisionAuditRepository:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    def append(self, decision, expert_decisions) -> None:
        data = []
        if self.path.exists():
            data = json.loads(self.path.read_text(encoding="utf-8"))

        data.append({
            "subject_id": decision.subject_id,
            "final_recommendation": decision.final_recommendation,
            "confidence": decision.confidence,
            "risk": decision.risk,
            "consensus_score": decision.consensus_score,
            "approved": decision.approved,
            "dissenting_experts": list(decision.dissenting_experts),
            "rationale": list(decision.rationale),
            "experts": [
                {
                    "expert": item.expert,
                    "recommendation": item.recommendation,
                    "confidence": item.confidence,
                    "risk": item.risk,
                    "rationale": item.rationale,
                    "category": item.category,
                }
                for item in expert_decisions
            ],
        })

        self.path.parent.mkdir(parents=True, exist_ok=True)
        temp = self.path.with_suffix(self.path.suffix + ".tmp")
        temp.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp.replace(self.path)

    def list_for_subject(self, subject_id: str) -> tuple[dict, ...]:
        if not self.path.exists():
            return ()
        data = json.loads(self.path.read_text(encoding="utf-8"))
        return tuple(
            item for item in data
            if item["subject_id"] == subject_id
        )
