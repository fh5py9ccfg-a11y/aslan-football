from dataclasses import dataclass

import json
from datetime import datetime

from sqlalchemy import text

from .comeback_prediction_mapper import sportmonks_predictions_to_comeback_inputs
from .db import SessionLocal


@dataclass(frozen=True)
class ProviderSyncReport:
    fetched: int
    published: int
    failed: int


class SportmonksFixtureSyncService:
    def __init__(self, *, client, publisher, predictions_enabled=False):
        self.client = client
        self.publisher = publisher
        self.predictions_enabled = bool(predictions_enabled)

    async def _enrich_predictions(self, fixture):
        if not self.predictions_enabled:
            return fixture
        fixture_id = str(fixture.get("id") or "")
        if not fixture_id:
            return fixture
        try:
            predictions = await self.client.predictions_by_fixture(fixture_id)
            features = sportmonks_predictions_to_comeback_inputs(predictions)
            enriched = dict(fixture)
            enriched["sportmonks_predictions"] = list(predictions)
            if features:
                enriched["comeback_inputs"] = features
            enriched.setdefault("meta", {})
            if isinstance(enriched["meta"], dict):
                enriched["meta"]["comeback_predictions_available"] = bool(features)
            return enriched
        except Exception as exc:
            enriched = dict(fixture)
            enriched.setdefault("meta", {})
            if isinstance(enriched["meta"], dict):
                enriched["meta"]["comeback_predictions_available"] = False
                enriched["meta"]["comeback_predictions_error"] = str(exc)[:300]
            return enriched

    async def sync_between(
        self, *, start_date, end_date,
        include="participants;scores;state;league", max_pages=100,
    ):
        fetched = published = failed = 0
        async for raw_fixture in self.client.iter_fixtures_between(
            start_date, end_date, include=include, max_pages=max_pages
        ):
            fetched += 1
            try:
                fixture = await self._enrich_predictions(raw_fixture)
                fixture_id = str(fixture["id"])
                participants = fixture.get("participants") or []

                home_team = next(
                    (
                        p.get("name")
                        for p in participants
                        if (p.get("meta") or {}).get("location") == "home"
                    ),
                    None,
                )
                away_team = next(
                    (
                        p.get("name")
                        for p in participants
                        if (p.get("meta") or {}).get("location") == "away"
                    ),
                    None,
                )

                if not home_team and len(participants) > 0:
                    home_team = participants[0].get("name")
                if not away_team and len(participants) > 1:
                    away_team = participants[1].get("name")

                starting_at = fixture.get("starting_at")
                kickoff_at = None
                if starting_at:
                    try:
                        kickoff_at = datetime.fromisoformat(
                            str(starting_at).replace("Z", "+00:00")
                        )
                    except ValueError:
                        kickoff_at = None

                state = fixture.get("state") or {}
                status = state.get("name") or state.get("state") or "scheduled"
                league = fixture.get("league") or {}
                league_name = league.get("name")

                with SessionLocal.begin() as session:
                    session.execute(
                        text(
                            """
                            INSERT INTO fixtures (
                                fixture_id, provider, provider_fixture_id,
                                league_name, home_team, away_team,
                                kickoff_at, status, raw_json
                            )
                            VALUES (
                                :fixture_id, 'sportmonks', :provider_fixture_id,
                                :league_name, :home_team, :away_team,
                                :kickoff_at, :status, :raw_json
                            )
                            ON CONFLICT (provider, provider_fixture_id)
                            DO UPDATE SET
                                league_name = EXCLUDED.league_name,
                                home_team = EXCLUDED.home_team,
                                away_team = EXCLUDED.away_team,
                                kickoff_at = EXCLUDED.kickoff_at,
                                status = EXCLUDED.status,
                                raw_json = EXCLUDED.raw_json,
                                updated_at = NOW()
                            """
                        ),
                        {
                            "fixture_id": fixture_id,
                            "provider_fixture_id": fixture_id,
                            "league_name": league_name,
                            "home_team": home_team or "Unknown",
                            "away_team": away_team or "Unknown",
                            "kickoff_at": kickoff_at,
                            "status": status,
                            "raw_json": json.dumps(
                                fixture,
                                ensure_ascii=False,
                                default=str,
                            ),
                        },
                    )

                await self.publisher.publish(
                    "provider.fixtures",
                    fixture,
                    f"sportmonks:fixture:{fixture_id}",
                )
                published += 1
            except Exception:
                failed += 1
        return ProviderSyncReport(fetched, published, failed)
