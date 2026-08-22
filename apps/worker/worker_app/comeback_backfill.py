from __future__ import annotations

import asyncio
import json
import os
from datetime import date, timedelta

from sqlalchemy import text

from .comeback_odds_mapper import sportmonks_odds_to_comeback_inputs
from .db import SessionLocal
from .sportmonks import SportmonksClient


async def backfill_day(client: SportmonksClient, day: date) -> tuple[int, int]:
    scanned = stored = 0
    async for fixture in client.iter_fixtures_between(
        day.isoformat(), day.isoformat(),
        include="participants;scores;state;league;events",
        max_pages=100,
    ):
        scanned += 1
        fixture_id = str(fixture.get("id") or "")
        if not fixture_id:
            continue
        try:
            odds = await client.prematch_odds_by_fixture(fixture_id)
            features = sportmonks_odds_to_comeback_inputs(odds)
        except Exception:
            continue
        required = {
            "home_win_probability", "draw_probability", "away_win_probability",
            "first_half_home_probability", "first_half_draw_probability", "first_half_away_probability",
        }
        if not required.issubset(features):
            continue
        raw = dict(fixture)
        raw["comeback_inputs"] = features
        raw.setdefault("meta", {})
        if isinstance(raw["meta"], dict):
            raw["meta"]["comeback_backfilled"] = True
        participants = fixture.get("participants") or []
        home = next((p.get("name") for p in participants if (p.get("meta") or {}).get("location") == "home"), "Unknown")
        away = next((p.get("name") for p in participants if (p.get("meta") or {}).get("location") == "away"), "Unknown")
        state = fixture.get("state") or {}
        status = state.get("name") or state.get("state") or "finished"
        league = fixture.get("league") or {}
        starting_at = fixture.get("starting_at")
        with SessionLocal.begin() as session:
            session.execute(text("""
                INSERT INTO fixtures (fixture_id,provider,provider_fixture_id,league_name,home_team,away_team,kickoff_at,status,raw_json)
                VALUES (:id,'sportmonks',:id,:league,:home,:away,:kickoff,:status,:raw)
                ON CONFLICT (provider,provider_fixture_id) DO UPDATE SET raw_json=EXCLUDED.raw_json,status=EXCLUDED.status,updated_at=NOW()
            """), {"id":fixture_id,"league":league.get("name"),"home":home,"away":away,"kickoff":starting_at,"status":status,"raw":json.dumps(raw,ensure_ascii=False,default=str)})
            for seq, event in enumerate(fixture.get("events") or (), start=1):
                if str(event.get("type") or "").lower() not in {"goal","own-goal","penalty"}:
                    continue
                minute = int(event.get("minute") or 0)
                participant_id = event.get("participant_id")
                home_id = next((p.get("id") for p in participants if (p.get("meta") or {}).get("location") == "home"), None)
                team = "HOME" if participant_id == home_id else "AWAY"
                session.execute(text("""
                    INSERT INTO match_events (fixture_id,sequence,event_type,minute,team)
                    VALUES (:id,:seq,'GOAL',:minute,:team)
                    ON CONFLICT (fixture_id,sequence) DO NOTHING
                """), {"id":fixture_id,"seq":seq,"minute":minute,"team":team})
        stored += 1
    return scanned, stored


async def run() -> None:
    client = SportmonksClient(api_token=os.environ["SPORTMONKS_API_TOKEN"])
    days = max(30, int(os.getenv("COMEBACK_BACKFILL_DAYS", "730")))
    target = max(100, int(os.getenv("COMEBACK_BACKFILL_TARGET", "150")))
    stored_total = 0
    try:
        for offset in range(1, days + 1):
            _, stored = await backfill_day(client, date.today() - timedelta(days=offset))
            stored_total += stored
            if stored_total >= target:
                break
            await asyncio.sleep(0.05)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(run())
