from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfidenceAdjustment:
    base_confidence: float
    provider_trust: int
    data_quality: int
    adjusted_confidence: float
    reason: str


class PredictionConfidenceAdjuster:
    def adjust(
        self,
        *,
        base_confidence: float,
        provider_trust: int,
        data_quality: int,
    ) -> ConfidenceAdjustment:
        if not 0 <= base_confidence <= 1:
            raise ValueError(
                "base_confidence 0 ile 1 arasında olmalıdır"
            )

        trust_factor = max(
            0.0,
            min(1.0, provider_trust / 100),
        )
        quality_factor = max(
            0.0,
            min(1.0, data_quality / 100),
        )
        combined_factor = (
            0.55 * trust_factor
            + 0.45 * quality_factor
        )
        adjusted = round(
            base_confidence * combined_factor,
            6,
        )

        return ConfidenceAdjustment(
            base_confidence=base_confidence,
            provider_trust=provider_trust,
            data_quality=data_quality,
            adjusted_confidence=adjusted,
            reason=(
                "Provider güveni ve veri kalitesi "
                "ile confidence kalibre edildi"
            ),
        )
