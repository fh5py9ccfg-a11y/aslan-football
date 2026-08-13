from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LeagueTranslationReport:
    score: float
    expected_level: float
    adaptation_penalty: float
    label: str

class LeagueTranslationModel:
    def evaluate(
        self,
        *,
        player_level: float,
        source_strength: float,
        target_strength: float,
        adaptation_risk: float,
    ) -> LeagueTranslationReport:
        for value in (
            player_level,
            source_strength,
            target_strength,
            adaptation_risk,
        ):
            if not 0 <= value <= 1:
                raise ValueError("Lig dönüşüm girdileri geçersiz")

        difficulty_gap = max(0.0, target_strength - source_strength)
        adaptation_penalty = min(
            1.0,
            difficulty_gap * 0.55 + adaptation_risk * 0.45,
        )
        expected_level = max(
            0.0,
            player_level * (1.0 - adaptation_penalty * 0.35),
        )
        score = max(
            0.0,
            min(expected_level * (1.0 - adaptation_penalty * 0.20), 1.0),
        )

        if score >= 0.75:
            label = "STRONG_TRANSLATION"
        elif score >= 0.58:
            label = "MODERATE_TRANSLATION"
        else:
            label = "HIGH_TRANSLATION_RISK"

        return LeagueTranslationReport(
            score=score,
            expected_level=expected_level,
            adaptation_penalty=adaptation_penalty,
            label=label,
        )
