from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExpertDecision:
    expert: str
    recommendation: str
    confidence: float
    risk: float
    rationale: str
    category: str

    def validate(self) -> None:
        if not self.expert.strip() or not self.recommendation.strip():
            raise ValueError("Uzman ve öneri alanları boş olamaz")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence geçersiz")
        if not 0 <= self.risk <= 1:
            raise ValueError("risk geçersiz")
        if not self.category.strip():
            raise ValueError("category boş olamaz")

@dataclass(frozen=True)
class OrchestratedDecision:
    subject_id: str
    final_recommendation: str
    confidence: float
    risk: float
    consensus_score: float
    dissenting_experts: tuple[str, ...]
    rationale: tuple[str, ...]
    approved: bool

@dataclass(frozen=True)
class KnowledgeRelation:
    source_id: str
    relation: str
    target_id: str
    weight: float
    metadata: dict

    def validate(self) -> None:
        if not self.source_id.strip() or not self.target_id.strip():
            raise ValueError("İlişki düğümleri boş olamaz")
        if not self.relation.strip():
            raise ValueError("relation boş olamaz")
        if not 0 <= self.weight <= 1:
            raise ValueError("weight geçersiz")
