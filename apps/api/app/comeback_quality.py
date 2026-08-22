from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


@dataclass(frozen=True)
class ComebackQuality:
    quality_score: int
    evidence_score: int
    conflict_penalty: int
    sample_penalty: int
    label: str
    reasons: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


def evaluate_candidate_quality(fixture: Mapping[str, Any], detector_result: Mapping[str, Any]) -> ComebackQuality:
    inputs = dict(fixture.get("comeback_inputs") or {})
    preferred = detector_result.get("preferred_market")
    raw_score = float(detector_result.get("score_2_1") if preferred == "2/1" else detector_result.get("score_1_2") or 0)

    evidence = 0.0
    reasons: list[str] = []

    required = (
        "home_win_probability", "draw_probability", "away_win_probability",
        "first_half_home_probability", "first_half_draw_probability", "first_half_away_probability",
    )
    market_complete = all(key in inputs for key in required)
    if market_complete:
        evidence += 0.35
        reasons.append("FT and first-half 1X2 profile is complete.")

    history_ready = bool(fixture.get("history_ready"))
    if history_ready:
        evidence += 0.25
        reasons.append("Both teams have historical comeback profiles.")

    similar_matches = int(inputs.get("similar_matches") or 0)
    if similar_matches >= 40:
        evidence += 0.20
        reasons.append(f"Strong similar-market sample ({similar_matches}).")
    elif similar_matches >= 20:
        evidence += 0.12
        reasons.append(f"Usable similar-market sample ({similar_matches}).")

    direct_key = "direct_2_1_probability" if preferred == "2/1" else "direct_1_2_probability"
    if inputs.get(direct_key) is not None:
        evidence += 0.20
        reasons.append("Direct provider HT/FT probability is available.")

    sample_penalty = 0
    if similar_matches < 10:
        sample_penalty += 10
    elif similar_matches < 20:
        sample_penalty += 5

    conflict_penalty = 0
    if preferred == "2/1":
        direct = float(inputs.get("direct_2_1_probability") or 0)
        similar = float(inputs.get("similar_2_1_rate") or 0)
    else:
        direct = float(inputs.get("direct_1_2_probability") or 0)
        similar = float(inputs.get("similar_1_2_rate") or 0)
    if direct and similar and abs(direct - similar) >= 0.10:
        conflict_penalty += 8
        reasons.append("Direct and neighbour HT/FT signals conflict materially.")

    evidence_score = int(round(_clamp(evidence) * 100))
    quality = int(round(0.65 * raw_score + 0.35 * evidence_score)) - sample_penalty - conflict_penalty
    quality = max(0, min(100, quality))

    if quality >= 85:
        label = "A"
    elif quality >= 75:
        label = "B"
    elif quality >= 65:
        label = "C"
    else:
        label = "LOW_CONFIDENCE"

    return ComebackQuality(
        quality_score=quality,
        evidence_score=evidence_score,
        conflict_penalty=conflict_penalty,
        sample_penalty=sample_penalty,
        label=label,
        reasons=tuple(reasons),
    )
