from __future__ import annotations

from .domain import ExplanationFactor, NormalizedFactor

class ContributionNormalizer:
    def normalize(
        self,
        factors: list[ExplanationFactor],
    ) -> tuple[NormalizedFactor, ...]:
        if not factors:
            raise ValueError("En az bir açıklama faktörü gerekir")

        for factor in factors:
            factor.validate()

        total = sum(
            abs(factor.raw_effect) * factor.confidence
            for factor in factors
        )
        if total == 0:
            equal = 1.0 / len(factors)
            return tuple(
                NormalizedFactor(
                    name=factor.name,
                    signed_share=0.0,
                    absolute_share=equal,
                    confidence=factor.confidence,
                    category=factor.category,
                )
                for factor in factors
            )

        normalized = []
        for factor in factors:
            weighted = factor.raw_effect * factor.confidence
            absolute = abs(weighted) / total
            signed = weighted / total
            normalized.append(
                NormalizedFactor(
                    name=factor.name,
                    signed_share=signed,
                    absolute_share=absolute,
                    confidence=factor.confidence,
                    category=factor.category,
                )
            )

        return tuple(
            sorted(
                normalized,
                key=lambda item: (-item.absolute_share, item.name),
            )
        )
