from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from sqlalchemy import select

from .db import SessionLocal
from .models import FixtureModel, MatchEventModel


MARKET_KEYS = (
    "home_win_probability",
    "draw_probability",
    "away_win_probability",
    "first_half_home_probability",
    "first_half_draw_probability",
    "first_half_away_probability",
)

FINISHED_STATUSES = {
    "finished", "ft", "after extra time", "after penalties", "aet", "pen"
}


@dataclass(frozen=True)
class SimilarMarketEvidence:
    matches: int
    two_one_matches: int
    one_two_matches: int
    two_one_rate: float
    one_two_rate: float
    mean_distance: float | None

    def as_dict(self) -> dict:
        return asdict(self)


def _parse_raw(raw_json: str | None) -> dict[str, Any]:
    if not raw_json:
        return {}
    try:
        value = json.loads(raw_json)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _feature_source(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("comeback_inputs", "prediction_features", "market_features"):
        value = raw.get(key)
        if isinstance(value, Mapping):
            return value
    meta = raw.get("meta")
    if isinstance(meta, Mapping):
        value = meta.get("comeback_inputs")
        if isinstance(value, Mapping):
            return value
    return {}


def _vector(source: Mapping[str, Any]) -> tuple[float, ...] | None:
    values: list[float] = []
    for key in MARKET_KEYS:
        try:
            value = float(source[key])
        except (KeyError, TypeError, ValueError):
            return None
        if value > 1.0:
            value /= 100.0
        if value < 0.0 or value > 1.0:
            return None
        values.append(value)
    return tuple(values)


def _distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    # FT profile carries slightly more weight than FH profile.
    weights = (1.25, 0.9, 1.25, 1.0, 0.8, 1.0)
    total = sum(w * (a - b) ** 2 for a, b, w in zip(left, right, weights))
    return math.sqrt(total / sum(weights))


def _outcome_from_events(events: Iterable[MatchEventModel]) -> tuple[str, str]:
    home_ht = away_ht = home_ft = away_ft = 0
    for event in events:
        side = str(event.team or "").upper()
        if side not in {"HOME", "AWAY"}:
            continue
        minute = int(event.minute or 0)
        if side == "HOME":
            home_ft += 1
            if minute <= 45:
                home_ht += 1
        else:
            away_ft += 1
            if minute <= 45:
                away_ht += 1

    def result(home: int, away: int) -> str:
        if home > away:
            return "HOME"
        if away > home:
            return "AWAY"
        return "DRAW"

    return result(home_ht, away_ht), result(home_ft, away_ft)


def similar_market_evidence(
    target_inputs: Mapping[str, Any],
    *,
    lookback_days: int = 1460,
    neighbors: int = 80,
    max_distance: float = 0.22,
    exclude_fixture_id: str | None = None,
) -> SimilarMarketEvidence:
    target = _vector(target_inputs)
    if target is None:
        return SimilarMarketEvidence(0, 0, 0, 0.0, 0.0, None)

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max(90, int(lookback_days)))

    with SessionLocal() as session:
        fixtures = session.execute(
            select(FixtureModel).where(
                FixtureModel.kickoff_at >= cutoff,
                FixtureModel.kickoff_at < now,
            )
        ).scalars().all()

        candidates: list[tuple[float, FixtureModel]] = []
        for fixture in fixtures:
            if exclude_fixture_id and fixture.fixture_id == exclude_fixture_id:
                continue
            if str(fixture.status or "").strip().lower() not in FINISHED_STATUSES:
                continue
            raw = _parse_raw(fixture.raw_json)
            vec = _vector(_feature_source(raw))
            if vec is None:
                continue
            distance = _distance(target, vec)
            if distance <= float(max_distance):
                candidates.append((distance, fixture))

        candidates.sort(key=lambda pair: pair[0])
        chosen = candidates[: max(1, int(neighbors))]
        fixture_ids = [fixture.fixture_id for _, fixture in chosen]
        if not fixture_ids:
            return SimilarMarketEvidence(0, 0, 0, 0.0, 0.0, None)

        events = session.execute(
            select(MatchEventModel).where(
                MatchEventModel.fixture_id.in_(fixture_ids),
                MatchEventModel.event_type == "GOAL",
            )
        ).scalars().all()

    grouped: dict[str, list[MatchEventModel]] = {fixture_id: [] for fixture_id in fixture_ids}
    for event in events:
        grouped.setdefault(event.fixture_id, []).append(event)

    two_one = one_two = 0
    for _, fixture in chosen:
        ht, ft = _outcome_from_events(grouped.get(fixture.fixture_id, ()))
        if ht == "AWAY" and ft == "HOME":
            two_one += 1
        elif ht == "HOME" and ft == "AWAY":
            one_two += 1

    count = len(chosen)
    mean_distance = sum(distance for distance, _ in chosen) / count if count else None
    return SimilarMarketEvidence(
        matches=count,
        two_one_matches=two_one,
        one_two_matches=one_two,
        two_one_rate=(two_one / count if count else 0.0),
        one_two_rate=(one_two / count if count else 0.0),
        mean_distance=(round(mean_distance, 6) if mean_distance is not None else None),
    )


def enrich_fixtures_with_neighbors(
    fixtures: list[dict],
    *,
    neighbors: int = 80,
    max_distance: float = 0.22,
    lookback_days: int = 1460,
) -> list[dict]:
    enriched: list[dict] = []
    for fixture in fixtures:
        item = dict(fixture)
        inputs = dict(item.get("comeback_inputs") or {})
        evidence = similar_market_evidence(
            inputs,
            neighbors=neighbors,
            max_distance=max_distance,
            lookback_days=lookback_days,
            exclude_fixture_id=str(item.get("fixture_id") or "") or None,
        )
        if evidence.matches:
            inputs["similar_matches"] = evidence.matches
            inputs["similar_2_1_rate"] = evidence.two_one_rate
            inputs["similar_1_2_rate"] = evidence.one_two_rate
            item["similar_market_evidence"] = evidence.as_dict()
        item["comeback_inputs"] = inputs
        item["neighbors_ready"] = evidence.matches > 0
        enriched.append(item)
    return enriched
