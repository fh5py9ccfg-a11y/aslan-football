from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Iterable, Mapping

from .comeback_detector import ComebackDetector, ComebackInputs


@dataclass(frozen=True)
class ComebackCandidate:
    fixture_id: str
    home_team: str
    away_team: str
    kickoff: str | None
    preferred_market: str
    score: int
    turnaround_potential: int
    score_2_1: int
    score_1_2: int
    label: str
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


class ComebackScanner:
    """Ranks fixture payloads using the HT/FT comeback detector.

    Expected fixture keys:
      fixture_id, home_team, away_team, kickoff and either a nested
      ``comeback_inputs`` mapping or the ComebackInputs fields at top level.

    Fixtures without enough data are skipped rather than guessed.
    """

    REQUIRED = {
        "home_win_probability",
        "draw_probability",
        "away_win_probability",
        "first_half_home_probability",
        "first_half_draw_probability",
        "first_half_away_probability",
    }

    def __init__(self, *, alert_threshold: int = 75, min_similar_matches: int = 20):
        self.detector = ComebackDetector(
            alert_threshold=alert_threshold,
            min_similar_matches=min_similar_matches,
        )

    def scan(self, fixtures: Iterable[Mapping[str, object]], *, limit: int = 10) -> list[dict]:
        candidates: list[ComebackCandidate] = []

        for fixture in fixtures:
            raw_inputs = fixture.get("comeback_inputs")
            if isinstance(raw_inputs, Mapping):
                payload = dict(raw_inputs)
            else:
                payload = dict(fixture)

            if not self.REQUIRED.issubset(payload):
                continue

            try:
                inputs = ComebackInputs(**{
                    field: payload[field]
                    for field in ComebackInputs.__dataclass_fields__
                    if field in payload
                })
                signal = self.detector.evaluate(inputs)
            except (TypeError, ValueError):
                continue

            if signal.preferred_market is None:
                continue

            score = signal.score_2_1 if signal.preferred_market == "2/1" else signal.score_1_2
            candidates.append(
                ComebackCandidate(
                    fixture_id=str(fixture.get("fixture_id") or fixture.get("id") or ""),
                    home_team=str(fixture.get("home_team") or fixture.get("home_name") or "Ev Takımı"),
                    away_team=str(fixture.get("away_team") or fixture.get("away_name") or "Deplasman Takımı"),
                    kickoff=(str(fixture.get("kickoff")) if fixture.get("kickoff") is not None else None),
                    preferred_market=signal.preferred_market,
                    score=score,
                    turnaround_potential=signal.turnaround_potential,
                    score_2_1=signal.score_2_1,
                    score_1_2=signal.score_1_2,
                    label=signal.label,
                    reasons=signal.reasons,
                    warnings=signal.warnings,
                )
            )

        candidates.sort(
            key=lambda item: (item.score, item.turnaround_potential),
            reverse=True,
        )
        return [item.as_dict() for item in candidates[: max(1, int(limit))]]


def scan_comeback_candidates(
    fixtures: Iterable[Mapping[str, object]],
    *,
    alert_threshold: int = 75,
    min_similar_matches: int = 20,
    limit: int = 10,
) -> list[dict]:
    return ComebackScanner(
        alert_threshold=alert_threshold,
        min_similar_matches=min_similar_matches,
    ).scan(fixtures, limit=limit)
