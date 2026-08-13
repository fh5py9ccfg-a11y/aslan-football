from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CandidateValue:
    provider: str
    value: Any
    trust_weight: float
    observed_at_epoch: int


@dataclass(frozen=True)
class ConsensusDecision:
    accepted: bool
    value: Any | None
    confidence: float
    reason: str
    supporting_providers: tuple[str, ...]


class SourceReconciler:
    def __init__(self, minimum_support_weight: float = 1.5):
        if minimum_support_weight <= 0:
            raise ValueError("minimum_support_weight pozitif olmalıdır")
        self.minimum_support_weight = minimum_support_weight

    def decide(self, candidates: list[CandidateValue]) -> ConsensusDecision:
        if not candidates:
            return ConsensusDecision(
                accepted=False,
                value=None,
                confidence=0.0,
                reason="Karşılaştırılacak kaynak verisi yok.",
                supporting_providers=(),
            )

        grouped: dict[str, dict[str, Any]] = {}
        for candidate in candidates:
            key = repr(candidate.value)
            bucket = grouped.setdefault(
                key,
                {"value": candidate.value, "weight": 0.0, "providers": [], "latest": 0},
            )
            bucket["weight"] += max(candidate.trust_weight, 0.0)
            bucket["providers"].append(candidate.provider)
            bucket["latest"] = max(bucket["latest"], candidate.observed_at_epoch)

        winner = max(
            grouped.values(),
            key=lambda item: (item["weight"], item["latest"], len(item["providers"])),
        )
        total_weight = sum(item["weight"] for item in grouped.values())
        confidence = 0.0 if total_weight <= 0 else winner["weight"] / total_weight

        accepted = winner["weight"] >= self.minimum_support_weight
        return ConsensusDecision(
            accepted=accepted,
            value=winner["value"] if accepted else None,
            confidence=round(confidence, 4),
            reason=(
                "Kaynaklar yeterli ağırlıkla uzlaştı."
                if accepted
                else "Kaynak uzlaşması güven eşiğinin altında."
            ),
            supporting_providers=tuple(sorted(set(winner["providers"]))),
        )
