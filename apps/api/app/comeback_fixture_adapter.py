from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Mapping

from sqlalchemy import select

from .comeback_history import enrich_fixtures_with_history
from .db import SessionLocal
from .models import FixtureModel


REQUIRED_MARKET_FIELDS = (
    "home_win_probability",
    "draw_probability",
    "away_win_probability",
    "first_half_home_probability",
    "first_half_draw_probability",
    "first_half_away_probability",
)

OPTIONAL_SIGNAL_FIELDS = (
    "home_comeback_rate_when_behind",
    "away_comeback_rate_when_behind",
    "home_loss_rate_when_ahead",
    "away_loss_rate_when_ahead",
    "home_second_half_goal_share",
    "away_second_half_goal_share",
    "historical_2_1_rate",
    "historical_1_2_rate",
    "similar_matches",
    "similar_2_1_rate",
    "similar_1_2_rate",
    "home_ft_shortening",
    "away_ft_shortening",
    "direct_2_1_probability",
    "direct_1_2_probability",
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _first_mapping(*values: object) -> Mapping[str, Any]:
    for value in values:
        if isinstance(value, Mapping):
            return value
    return {}


def _parse_raw(raw_json: str | None) -> dict[str, Any]:
    if not raw_json:
        return {}
    try:
        value = json.loads(raw_json)
    except (TypeError, ValueError):
        return {}
    return value if isinstance(value, dict) else {}


def _number(source: Mapping[str, Any], key: str) -> float | int | None:
    value = source.get(key)
    if value is None:
        return None
    try:
        if key == "similar_matches":
            return int(value)
        return float(value)
    except (TypeError, ValueError):
        return None


def _extract_comeback_inputs(raw: Mapping[str, Any]) -> dict[str, Any]:
    """Extract precomputed model/market signals without inventing values."""
    source = _first_mapping(
        raw.get("comeback_inputs"),
        raw.get("prediction_features"),
        raw.get("market_features"),
        _mapping(raw.get("meta")).get("comeback_inputs"),
    )

    result: dict[str, Any] = {}
    for key in (*REQUIRED_MARKET_FIELDS, *OPTIONAL_SIGNAL_FIELDS):
        value = _number(source, key)
        if value is not None:
            result[key] = value
    return result


def fixture_to_comeback_payload(item: FixtureModel) -> dict[str, Any]:
    raw = _parse_raw(item.raw_json)
    inputs = _extract_comeback_inputs(raw)
    missing = [key for key in REQUIRED_MARKET_FIELDS if key not in inputs]

    kickoff = item.kickoff_at
    if kickoff is not None:
        try:
            kickoff_text = kickoff.isoformat()
        except AttributeError:
            kickoff_text = str(kickoff)
    else:
        kickoff_text = None

    return {
        "fixture_id": item.fixture_id,
        "provider": item.provider,
        "provider_fixture_id": item.provider_fixture_id,
        "league_name": item.league_name,
        "home_team": item.home_team,
        "away_team": item.away_team,
        "kickoff": kickoff_text,
        "status": item.status,
        "comeback_inputs": inputs,
        "data_ready": not missing,
        "missing_fields": missing,
    }


def load_comeback_fixtures(
    *,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = 500,
    history_lookback_days: int = 730,
) -> list[dict[str, Any]]:
    now = datetime.now(timezone.utc)
    start = start or now.replace(hour=0, minute=0, second=0, microsecond=0)

    with SessionLocal() as session:
        statement = (
            select(FixtureModel)
            .where(FixtureModel.kickoff_at >= start)
            .order_by(FixtureModel.kickoff_at.asc())
            .limit(max(1, min(int(limit), 2000)))
        )
        if end is not None:
            statement = statement.where(FixtureModel.kickoff_at < end)
        items = session.execute(statement).scalars().all()

    fixtures = [fixture_to_comeback_payload(item) for item in items]
    return enrich_fixtures_with_history(
        fixtures,
        lookback_days=history_lookback_days,
    )


def comeback_data_readiness(fixtures: list[Mapping[str, Any]]) -> dict[str, Any]:
    total = len(fixtures)
    ready = sum(1 for item in fixtures if bool(item.get("data_ready")))
    history_ready = sum(1 for item in fixtures if bool(item.get("history_ready")))
    missing_counts = {key: 0 for key in REQUIRED_MARKET_FIELDS}
    direct_htft = sum(
        1
        for item in fixtures
        if any(
            key in (item.get("comeback_inputs") or {})
            for key in ("direct_2_1_probability", "direct_1_2_probability")
        )
    )
    for item in fixtures:
        for key in item.get("missing_fields", ()):
            if key in missing_counts:
                missing_counts[key] += 1

    return {
        "fixtures": total,
        "ready": ready,
        "not_ready": total - ready,
        "ready_ratio": (round(ready / total, 4) if total else 0.0),
        "history_ready": history_ready,
        "history_ready_ratio": (round(history_ready / total, 4) if total else 0.0),
        "direct_htft_ready": direct_htft,
        "direct_htft_ratio": (round(direct_htft / total, 4) if total else 0.0),
        "missing_counts": missing_counts,
    }
