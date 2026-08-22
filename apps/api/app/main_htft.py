"""Aslan Football API wrapper exposing a clean HTFT fixture feed.

The worker already enriches Sportmonks fixtures and stores normalized full-time
and first-half 1X2 probabilities in fixtures.raw_json -> comeback_inputs.
This wrapper turns those probabilities into fair decimal odds so Aslan Skor's
validated HTFT engine can consume them without manual data entry.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

from fastapi import Query
from sqlalchemy import text

from .main import app
from .db import SessionLocal


def _fair_odd(probability):
    try:
        p = float(probability)
    except (TypeError, ValueError):
        return None
    if not (0.0 < p < 1.0):
        return None
    return round(1.0 / p, 4)


def _odds_from_raw(raw_json: str) -> dict[str, float]:
    try:
        raw = json.loads(raw_json or "{}")
    except Exception:
        return {}
    features = raw.get("comeback_inputs") or {}
    mapping = {
        "MS1": "home_win_probability",
        "MSX": "draw_probability",
        "MS2": "away_win_probability",
        "İY1": "first_half_home_probability",
        "İYX": "first_half_draw_probability",
        "İY2": "first_half_away_probability",
    }
    out = {}
    for market, key in mapping.items():
        odd = _fair_odd(features.get(key))
        if odd:
            out[market] = odd
    return out


@app.get("/htft/feed")
def htft_feed(
    days: int = Query(default=2, ge=1, le=14),
    limit: int = Query(default=500, ge=1, le=1000),
):
    now = datetime.now(timezone.utc)
    until = now + timedelta(days=days)
    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT fixture_id, provider, provider_fixture_id, league_name,
                       home_team, away_team, kickoff_at, status, raw_json
                FROM fixtures
                WHERE kickoff_at IS NOT NULL
                  AND kickoff_at >= :now
                  AND kickoff_at < :until
                ORDER BY kickoff_at ASC
                LIMIT :limit
                """
            ),
            {"now": now, "until": until, "limit": limit},
        ).mappings().all()

    items = []
    skipped_without_odds = 0
    for row in rows:
        odds = _odds_from_raw(row.get("raw_json"))
        if len(odds) < 3:
            skipped_without_odds += 1
            continue
        kickoff = row.get("kickoff_at")
        items.append({
            "fixture_id": str(row.get("fixture_id") or ""),
            "provider": row.get("provider"),
            "provider_fixture_id": str(row.get("provider_fixture_id") or ""),
            "league": row.get("league_name"),
            "home": row.get("home_team"),
            "away": row.get("away_team"),
            "kickoff_at": kickoff.isoformat() if hasattr(kickoff, "isoformat") else str(kickoff or ""),
            "status": row.get("status"),
            "odds": odds,
            "market_count": len(odds),
        })

    return {
        "source": "sportmonks-fixtures-db",
        "generated_at": now.isoformat(),
        "days": days,
        "rows_considered": len(rows),
        "skipped_without_odds": skipped_without_odds,
        "count": len(items),
        "fixtures": items,
    }
