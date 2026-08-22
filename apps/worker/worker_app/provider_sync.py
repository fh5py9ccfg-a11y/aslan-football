from dataclasses import dataclass
import asyncio
import json
from datetime import datetime
from sqlalchemy import text
from .comeback_prediction_mapper import sportmonks_predictions_to_comeback_inputs
from .comeback_odds_mapper import sportmonks_odds_to_comeback_inputs
from .db import SessionLocal


@dataclass(frozen=True)
class ProviderSyncReport:
    fetched: int
    published: int
    failed: int
    fixture_ids: tuple[str, ...] = ()


class SportmonksFixtureSyncService:
    def __init__(self, *, client, publisher, predictions_enabled=False, enrichment_concurrency=8):
        self.client = client
        self.publisher = publisher
        self.predictions_enabled = bool(predictions_enabled)
        self.enrichment_concurrency = max(1, min(int(enrichment_concurrency), 12))
        self._enrichment_gate = asyncio.Semaphore(self.enrichment_concurrency)

    async def _enrich_market_data(self, fixture):
        fixture_id = str(fixture.get("id") or "")
        if not fixture_id:
            return fixture
        enriched = dict(fixture)
        enriched.setdefault("meta", {})
        features = {}

        async with self._enrichment_gate:
            try:
                odds = await self.client.prematch_odds_by_fixture(fixture_id)
                features.update(sportmonks_odds_to_comeback_inputs(odds))
                enriched["sportmonks_prematch_odds_count"] = len(odds)
                enriched["meta"]["comeback_odds_available"] = bool(features)
                enriched["meta"]["comeback_odds_rows_returned"] = len(odds)
            except Exception as exc:
                enriched["meta"]["comeback_odds_available"] = False
                enriched["meta"]["comeback_odds_error"] = str(exc)[:300]

            if self.predictions_enabled:
                try:
                    predictions = await self.client.predictions_by_fixture(fixture_id)
                    predicted = sportmonks_predictions_to_comeback_inputs(predictions)
                    for key, value in predicted.items():
                        features.setdefault(key, value)
                    enriched["sportmonks_predictions"] = list(predictions)
                    enriched["meta"]["comeback_predictions_available"] = bool(predicted)
                except Exception as exc:
                    enriched["meta"]["comeback_predictions_available"] = False
                    enriched["meta"]["comeback_predictions_error"] = str(exc)[:300]

        if features:
            enriched["comeback_inputs"] = features
        return enriched

    async def _store_and_publish(self, raw_fixture):
        try:
            fixture = await self._enrich_market_data(raw_fixture)
            fixture_id = str(fixture["id"])
            participants = fixture.get("participants") or []
            home_team = next((p.get("name") for p in participants if (p.get("meta") or {}).get("location") == "home"), None)
            away_team = next((p.get("name") for p in participants if (p.get("meta") or {}).get("location") == "away"), None)
            if not home_team and len(participants) > 0:
                home_team = participants[0].get("name")
            if not away_team and len(participants) > 1:
                away_team = participants[1].get("name")

            kickoff_at = None
            starting_at = fixture.get("starting_at")
            if starting_at:
                try:
                    kickoff_at = datetime.fromisoformat(str(starting_at).replace("Z", "+00:00"))
                except ValueError:
                    pass

            state = fixture.get("state") or {}
            status = state.get("name") or state.get("state") or "scheduled"
            league = fixture.get("league") or {}
            with SessionLocal.begin() as session:
                session.execute(
                    text("""INSERT INTO fixtures (fixture_id,provider,provider_fixture_id,league_name,home_team,away_team,kickoff_at,status,raw_json) VALUES (:fixture_id,'sportmonks',:provider_fixture_id,:league_name,:home_team,:away_team,:kickoff_at,:status,:raw_json) ON CONFLICT (provider,provider_fixture_id) DO UPDATE SET league_name=EXCLUDED.league_name,home_team=EXCLUDED.home_team,away_team=EXCLUDED.away_team,kickoff_at=EXCLUDED.kickoff_at,status=EXCLUDED.status,raw_json=EXCLUDED.raw_json,updated_at=NOW()"""),
                    {
                        "fixture_id": fixture_id,
                        "provider_fixture_id": fixture_id,
                        "league_name": league.get("name"),
                        "home_team": home_team or "Unknown",
                        "away_team": away_team or "Unknown",
                        "kickoff_at": kickoff_at,
                        "status": status,
                        "raw_json": json.dumps(fixture, ensure_ascii=False, default=str),
                    },
                )
            await self.publisher.publish("provider.fixtures", fixture, f"sportmonks:fixture:{fixture_id}")
            return True, fixture_id
        except Exception:
            return False, None

    async def sync_between(self, *, start_date, end_date, include="participants;scores;state;league", max_pages=100):
        fetched = published = failed = 0
        synced_fixture_ids = []
        chunk = []
        chunk_size = self.enrichment_concurrency * 2

        async def flush(items):
            nonlocal published, failed
            if not items:
                return
            results = await asyncio.gather(*(self._store_and_publish(item) for item in items))
            for ok, fixture_id in results:
                if ok:
                    published += 1
                    if fixture_id:
                        synced_fixture_ids.append(fixture_id)
                else:
                    failed += 1

        async for raw_fixture in self.client.iter_fixtures_between(start_date, end_date, include=include, max_pages=max_pages):
            fetched += 1
            chunk.append(raw_fixture)
            if len(chunk) >= chunk_size:
                await flush(chunk)
                chunk = []

        await flush(chunk)
        return ProviderSyncReport(fetched, published, failed, tuple(synced_fixture_ids))
