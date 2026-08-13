from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class FootballDecisionContext:
    subject_id: str
    decision_type: str
    payload: dict
    reliability_score: float = 1.0

    def validate(self) -> None:
        if not self.subject_id.strip():
            raise ValueError("subject_id boş olamaz")
        if not self.decision_type.strip():
            raise ValueError("decision_type boş olamaz")
        if not isinstance(self.payload, dict):
            raise ValueError("payload sözlük olmalıdır")
        if not 0 <= self.reliability_score <= 1:
            raise ValueError("reliability_score geçersiz")
