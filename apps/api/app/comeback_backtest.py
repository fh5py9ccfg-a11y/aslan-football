from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Mapping

from sqlalchemy import select

from .comeback_detector import ComebackDetector, ComebackInputs
from .db import SessionLocal
from .models import FixtureModel, MatchEventModel


REQUIRED = (
    "home_win_probability",
    "draw_probability",
    "away_win_probability",
    "first_half_home_probability",
    "first_half_draw_probability",
    "first_half_away_probability",
)

FINISHED = {"finished", "ft", "after extra time", "after penalties", "aet", "pen"}


@dataclass(frozen=True)
class BacktestRow:
    fixture_id: str
    kickoff: str
    market: str
    score: int
    actual: bool



def _parse(raw_json: str | None) -> Mapping[str, Any]:
    if not raw_json:
        return {}
    try:
        value = json.loads(raw_json)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, Mapping) else {}


def _source(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("comeback_inputs", "prediction_features", "market_features"):
        value = raw.get(key)
        if isinstance(value, Mapping):
            return value
    meta = raw.get("meta")
    if isinstance(meta, Mapping) and isinstance(meta.get("comeback_inputs"), Mapping):
        return meta["comeback_inputs"]
    return {}


def _outcome(events: list[MatchEventModel]) -> tuple[str, str]:
    hh = ah = hf = af = 0
    for event in events:
        side = str(event.team or "").upper()
        if side not in {"HOME", "AWAY"}:
            continue
        minute = int(event.minute or 0)
        if side == "HOME":
            hf += 1
            if minute <= 45:
                hh += 1
        else:
            af += 1
            if minute <= 45:
                ah += 1

    def result(home: int, away: int) -> str:
        return "HOME" if home > away else "AWAY" if away > home else "DRAW"

    return result(hh, ah), result(hf, af)


def _safe_inputs(source: Mapping[str, Any]) -> ComebackInputs | None:
    if any(key not in source for key in REQUIRED):
        return None
    values: dict[str, Any] = {}
    for field in ComebackInputs.__dataclass_fields__:
        if field in source:
            values[field] = source[field]
    try:
        return ComebackInputs(**values)
    except (TypeError, ValueError):
        return None


def _calibration(rows: list[BacktestRow], market: str) -> list[dict[str, Any]]:
    market_rows = [row for row in rows if row.market == market]
    buckets = ((0, 59), (60, 69), (70, 74), (75, 79), (80, 84), (85, 89), (90, 100))
    result: list[dict[str, Any]] = []
    for low, high in buckets:
        chosen = [row for row in market_rows if low <= row.score <= high]
        if not chosen:
            continue
        hits = sum(row.actual for row in chosen)
        result.append({
            "score_band": f"{low}-{high}",
            "matches": len(chosen),
            "hits": hits,
            "actual_rate": round(hits / len(chosen), 4),
        })
    return result


def _threshold_table(rows: list[BacktestRow], market: str, baseline_rate: float) -> list[dict[str, Any]]:
    market_rows = [row for row in rows if row.market == market]
    result = []
    for threshold in (65, 70, 75, 80, 85, 90):
        chosen = [row for row in market_rows if row.score >= threshold]
        if not chosen:
            continue
        hits = sum(row.actual for row in chosen)
        rate = hits / len(chosen)
        result.append({
            "threshold": threshold,
            "selections": len(chosen),
            "hits": hits,
            "hit_rate": round(rate, 4),
            "lift_vs_baseline": round(rate / baseline_rate, 3) if baseline_rate > 0 else None,
        })
    return result


def run_comeback_backtest(*, lookback_days: int = 1460, min_matches: int = 100) -> dict[str, Any]:
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(days=max(90, int(lookback_days)))

    with SessionLocal() as session:
        fixtures = session.execute(
            select(FixtureModel)
            .where(FixtureModel.kickoff_at >= cutoff, FixtureModel.kickoff_at < now)
            .order_by(FixtureModel.kickoff_at.asc())
        ).scalars().all()
        fixtures = [f for f in fixtures if str(f.status or "").strip().lower() in FINISHED]
        ids = [f.fixture_id for f in fixtures]
        events = session.execute(
            select(MatchEventModel).where(
                MatchEventModel.fixture_id.in_(ids),
                MatchEventModel.event_type == "GOAL",
            )
        ).scalars().all() if ids else []

    grouped: dict[str, list[MatchEventModel]] = defaultdict(list)
    for event in events:
        grouped[event.fixture_id].append(event)

    detector = ComebackDetector(alert_threshold=0)
    rows: list[BacktestRow] = []
    base_21 = base_12 = eligible = 0

    for fixture in fixtures:
        inputs = _safe_inputs(_source(_parse(fixture.raw_json)))
        if inputs is None:
            continue
        ht, ft = _outcome(grouped.get(fixture.fixture_id, []))
        actual_21 = ht == "AWAY" and ft == "HOME"
        actual_12 = ht == "HOME" and ft == "AWAY"
        eligible += 1
        base_21 += int(actual_21)
        base_12 += int(actual_12)
        signal = detector.evaluate(inputs)
        kickoff = fixture.kickoff_at.isoformat() if fixture.kickoff_at else ""
        rows.append(BacktestRow(fixture.fixture_id, kickoff, "2/1", signal.score_2_1, actual_21))
        rows.append(BacktestRow(fixture.fixture_id, kickoff, "1/2", signal.score_1_2, actual_12))

    baseline_21 = base_21 / eligible if eligible else 0.0
    baseline_12 = base_12 / eligible if eligible else 0.0
    enough = eligible >= max(1, int(min_matches))

    return {
        "method": "chronological out-of-sample audit using stored pre-match features; no future outcome fields are injected",
        "eligible_matches": eligible,
        "minimum_required": int(min_matches),
        "enough_data": enough,
        "baseline": {
            "2/1": {"hits": base_21, "rate": round(baseline_21, 4)},
            "1/2": {"hits": base_12, "rate": round(baseline_12, 4)},
        },
        "thresholds": {
            "2/1": _threshold_table(rows, "2/1", baseline_21),
            "1/2": _threshold_table(rows, "1/2", baseline_12),
        },
        "calibration": {
            "2/1": _calibration(rows, "2/1"),
            "1/2": _calibration(rows, "1/2"),
        },
        "warning": None if enough else "Not enough stored pre-match feature history yet; do not tune weights from this sample.",
    }
