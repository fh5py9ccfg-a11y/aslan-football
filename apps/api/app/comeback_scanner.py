from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Mapping

from .comeback_detector import ComebackDetector, ComebackInputs
from .comeback_quality import evaluate_candidate_quality


@dataclass(frozen=True)
class ComebackCandidate:
    fixture_id: str
    home_team: str
    away_team: str
    kickoff: str | None
    preferred_market: str
    score: int
    applied_threshold: int
    quality_score: int
    quality_label: str
    evidence_score: int
    confidence_score: int
    qualified: bool
    qualification_reason: str
    turnaround_potential: int
    score_2_1: int
    score_1_2: int
    label: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


class ComebackScanner:
    REQUIRED = {
        "home_win_probability", "draw_probability", "away_win_probability",
        "first_half_home_probability", "first_half_draw_probability", "first_half_away_probability",
    }

    def __init__(self, *, alert_threshold: int = 75, threshold_2_1: int | None = None,
                 threshold_1_2: int | None = None, min_similar_matches: int = 20,
                 min_live_score: int = 55, min_quality_score: int = 45):
        self.detector = ComebackDetector(alert_threshold=0, min_similar_matches=min_similar_matches)
        self.threshold_2_1 = int(threshold_2_1 if threshold_2_1 is not None else alert_threshold)
        self.threshold_1_2 = int(threshold_1_2 if threshold_1_2 is not None else alert_threshold)
        self.min_live_score = int(min_live_score)
        self.min_quality_score = int(min_quality_score)

    def scan(self, fixtures: Iterable[Mapping[str, object]], *, limit: int = 10,
             ranking_only: bool = False) -> list[dict]:
        candidates: list[ComebackCandidate] = []
        for fixture in fixtures:
            raw_inputs = fixture.get("comeback_inputs")
            payload = dict(raw_inputs) if isinstance(raw_inputs, Mapping) else dict(fixture)
            if not self.REQUIRED.issubset(payload):
                continue
            try:
                inputs = ComebackInputs(**{field: payload[field] for field in ComebackInputs.__dataclass_fields__ if field in payload})
                signal = self.detector.evaluate(inputs)
            except (TypeError, ValueError):
                continue

            preferred = "2/1" if signal.score_2_1 >= signal.score_1_2 else "1/2"
            score = signal.score_2_1 if preferred == "2/1" else signal.score_1_2
            applied_threshold = self.threshold_2_1 if preferred == "2/1" else self.threshold_1_2

            signal_dict = signal.as_dict()
            signal_dict["preferred_market"] = preferred
            quality = evaluate_candidate_quality(fixture, signal_dict)

            # Evidence-aware confidence. Raw detector score alone is not enough for
            # a rare HT/FT reversal; low-evidence matches must not look actionable.
            confidence_score = int(round(
                0.55 * score + 0.30 * quality.quality_score + 0.15 * quality.evidence_score
            ))

            if score < self.min_live_score:
                qualified = False
                qualification_reason = f"raw_score<{self.min_live_score}"
            elif quality.quality_score < self.min_quality_score:
                qualified = False
                qualification_reason = f"quality<{self.min_quality_score}"
            elif score < applied_threshold:
                qualified = False
                qualification_reason = f"below_threshold<{applied_threshold}"
            else:
                qualified = True
                qualification_reason = "qualified"

            if not ranking_only and not qualified:
                continue

            if qualified and score >= 88:
                label = "VERY_STRONG"
            elif qualified and score >= 82:
                label = "STRONG"
            elif qualified:
                label = "WATCH"
            else:
                label = "RANK_ONLY"

            candidates.append(ComebackCandidate(
                fixture_id=str(fixture.get("fixture_id") or fixture.get("id") or ""),
                home_team=str(fixture.get("home_team") or fixture.get("home_name") or "Ev Takımı"),
                away_team=str(fixture.get("away_team") or fixture.get("away_name") or "Deplasman Takımı"),
                kickoff=str(fixture.get("kickoff")) if fixture.get("kickoff") is not None else None,
                preferred_market=preferred,
                score=score,
                applied_threshold=applied_threshold,
                quality_score=quality.quality_score,
                quality_label=quality.label,
                evidence_score=quality.evidence_score,
                confidence_score=confidence_score,
                qualified=qualified,
                qualification_reason=qualification_reason,
                turnaround_potential=signal.turnaround_potential,
                score_2_1=signal.score_2_1,
                score_1_2=signal.score_1_2,
                label=label,
                reasons=tuple(signal.reasons) + tuple(quality.reasons),
                warnings=signal.warnings,
            ))

        # Qualified signals first; within each group rank by confidence, then raw score.
        candidates.sort(
            key=lambda item: (
                1 if item.qualified else 0,
                item.confidence_score,
                item.score,
                item.quality_score,
                item.turnaround_potential,
            ),
            reverse=True,
        )
        return [item.as_dict() for item in candidates[:max(1, int(limit))]]


def scan_comeback_candidates(fixtures: Iterable[Mapping[str, object]], *, alert_threshold: int = 75,
                             threshold_2_1: int | None = None, threshold_1_2: int | None = None,
                             min_similar_matches: int = 20, limit: int = 10,
                             ranking_only: bool = False, min_live_score: int = 55,
                             min_quality_score: int = 45) -> list[dict]:
    return ComebackScanner(
        alert_threshold=alert_threshold,
        threshold_2_1=threshold_2_1,
        threshold_1_2=threshold_1_2,
        min_similar_matches=min_similar_matches,
        min_live_score=min_live_score,
        min_quality_score=min_quality_score,
    ).scan(fixtures, limit=limit, ranking_only=ranking_only)
