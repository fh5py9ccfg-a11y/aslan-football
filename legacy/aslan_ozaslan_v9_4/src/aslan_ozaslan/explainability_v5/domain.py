from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class ExplanationFactor:
    name: str
    raw_effect: float
    confidence: float
    category: str

    def validate(self) -> None:
        if not self.name.strip() or not self.category.strip():
            raise ValueError("Açıklama faktörü alanları boş olamaz")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence 0 ile 1 arasında olmalıdır")

@dataclass(frozen=True)
class NormalizedFactor:
    name: str
    signed_share: float
    absolute_share: float
    confidence: float
    category: str
