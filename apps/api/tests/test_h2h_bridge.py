from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import httpx
import pytest

from apps.api.app.h2h_bridge import (
    AmbiguousLookup,
    H2HFeedRequest,
    ProviderUnavailable,
    ResolvedFixture,
    SportmonksH2HClient,
    TTLCache,
    normalize_h2h_matches,
    resolve_fixture,
)


def _target() -> ResolvedFixture:
    return ResolvedFixture(
        resolved_by="fixture_id",
        fixture_id="local-900",
        provider_fixture_id="900",
        league="Test League",
        kickoff_at=datetime(2026, 8, 30, 18, 0, tzinfo=timezone.utc),
        home_id=10,
        home_name="Requested Home",
        away_id=20,
        away_name="Requested Away",
    )


def _score(description: str, participant_id: int, side: str, goals: int) -> dict:
    return {
        "description": description,
        "participant_id": participant_id,
        "score": {"participant": side, "goals": goals},
    }


def test_reversed_fixture_is_oriented_to_requested_home_and_uses_regulation_ft():
    fixture = {
        "id": 101,
        "starting_at": "2025-10-10 18:00:00",
        "league": {"name": "Cup"},
        "participants": [
            {"id": 20, "name": "Requested Away", "meta": {"location": "home"}},
            {"id": 10, "name": "Requested Home", "meta": {"location": "away"}},
        ],
        "scores": [
            _score("1ST_HALF", 20, "home", 0),
            _score("1ST_HALF", 10, "away", 1),
            _score("2ND_HALF", 20, "home", 2),
            _score("2ND_HALF", 10, "away", 1),
            # These must not contaminate regulation FT.
            _score("CURRENT", 20, "home", 3),
            _score("CURRENT", 10, "away", 3),
            _score("PENALTY_SHOOTOUT", 20, "home", 5),
            _score("PENALTY_SHOOTOUT", 10, "away", 4),
        ],
    }

    matches, skipped = normalize_h2h_matches([fixture], _target(), limit=8)

    assert skipped == 0
    assert len(matches) == 1
    item = matches[0]
    assert item["venue_orientation"] == "reversed"
    assert item["regulation_time"] is True
    assert item["ht"]["score"] == "1-0"
    assert item["ft"]["score"] == "1-2"
    assert item["result_from_requested_home"] == "L"


def test_current_only_score_is_skipped_when_regulation_ft_is_unproven():
    fixture = {
        "id": 102,
        "starting_at": "2025-09-01 18:00:00",
        "participants": [
            {"id": 10, "name": "Requested Home", "meta": {"location": "home"}},
            {"id": 20, "name": "Requested Away", "meta": {"location": "away"}},
        ],
        "scores": [
            _score("1ST_HALF", 10, "home", 1),
            _score("1ST_HALF", 20, "away", 1),
            _score("CURRENT", 10, "home", 2),
            _score("CURRENT", 20, "away", 2),
        ],
    }

    matches, skipped = normalize_h2h_matches([fixture], _target(), limit=8)

    assert matches == []
    assert skipped == 1


def test_ttl_cache_avoids_duplicate_provider_call():
    async def scenario():
        cache = TTLCache(ttl_seconds=600)
        calls = 0

        async def fetcher():
            nonlocal calls
            calls += 1
            return [{"id": 1}]

        first, first_hit = await cache.get_or_fetch("10:20", fetcher)
        second, second_hit = await cache.get_or_fetch("10:20", fetcher)
        return first, first_hit, second, second_hit, calls

    first, first_hit, second, second_hit, calls = asyncio.run(scenario())
    assert first == second == [{"id": 1}]
    assert first_hit is False
    assert second_hit is True
    assert calls == 1


def test_provider_uses_official_h2h_path_and_keeps_token_out_of_url():
    seen = {}

    def handler(request: httpx.Request) -> httpx.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers.get("Authorization")
        return httpx.Response(200, json={"data": []})

    async def scenario():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = SportmonksH2HClient(api_token="super-secret", client=http_client)
            return await client.fetch(10, 20)

    assert asyncio.run(scenario()) == []
    assert "/fixtures/head-to-head/10/20" in seen["url"]
    assert "api_token" not in seen["url"]
    assert "super-secret" not in seen["url"]
    assert seen["authorization"] == "super-secret"


def test_provider_error_does_not_echo_token_or_response_body():
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"message": "debug super-secret"})

    async def scenario():
        transport = httpx.MockTransport(handler)
        async with httpx.AsyncClient(transport=transport) as http_client:
            client = SportmonksH2HClient(api_token="super-secret", client=http_client)
            with pytest.raises(ProviderUnavailable) as caught:
                await client.fetch(10, 20)
            return str(caught.value)

    message = asyncio.run(scenario())
    assert "HTTP 500" in message
    assert "super-secret" not in message
    assert "debug" not in message


def _fixture_row(*, fixture_id: str, provider_fixture_id: str = "900") -> dict:
    return {
        "fixture_id": fixture_id,
        "provider_fixture_id": provider_fixture_id,
        "league_name": "Test League",
        "home_team": "Requested Home",
        "away_team": "Requested Away",
        "kickoff_at": datetime(2026, 8, 30, 18, 0, tzinfo=timezone.utc),
        "raw_json": {
            "participants": [
                {"id": 10, "name": "Requested Home", "meta": {"location": "home"}},
                {"id": 20, "name": "Requested Away", "meta": {"location": "away"}},
            ]
        },
    }


class _FakeResult:
    def __init__(self, rows):
        self._rows = rows

    def mappings(self):
        return self

    def all(self):
        return self._rows


class _FakeSession:
    def __init__(self, *, id_rows=(), day_rows=()):
        self.id_rows = list(id_rows)
        self.day_rows = list(day_rows)
        self.calls = []

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, _statement, params):
        self.calls.append(dict(params))
        if "fixture_id" in params:
            return _FakeResult(self.id_rows)
        return _FakeResult(self.day_rows)


def test_fixture_id_is_resolved_before_fallback():
    session = _FakeSession(
        id_rows=[_fixture_row(fixture_id="local-900")],
        day_rows=[
            _fixture_row(fixture_id="duplicate-a"),
            _fixture_row(fixture_id="duplicate-b"),
        ],
    )
    request = H2HFeedRequest(
        fixture_id="local-900",
        home="Requested Home",
        away="Requested Away",
        kickoff_at="2026-08-30T18:00:00Z",
        league="Test League",
    )

    resolved = resolve_fixture(lambda: session, request)

    assert resolved.resolved_by == "fixture_id"
    assert resolved.home_id == 10
    assert len(session.calls) == 1
    assert session.calls[0] == {"fixture_id": "local-900"}


def test_ambiguous_name_date_league_fallback_fails_closed():
    session = _FakeSession(
        day_rows=[
            _fixture_row(fixture_id="duplicate-a", provider_fixture_id="901"),
            _fixture_row(fixture_id="duplicate-b", provider_fixture_id="902"),
        ]
    )
    request = H2HFeedRequest(
        home="Requested Hôme",
        away="Requested Away",
        kickoff_at="2026-08-30T18:00:00Z",
        league="TEST-LEAGUE",
    )

    with pytest.raises(AmbiguousLookup):
        resolve_fixture(lambda: session, request)


def test_request_accepts_home_and_away_without_fixture_date_or_league():
    request = H2HFeedRequest(home="Requested Home", away="Requested Away")

    assert request.fixture_id is None
    assert request.kickoff_at is None
    assert request.league is None


def test_names_without_date_resolve_single_fixture_in_current_window():
    session = _FakeSession(day_rows=[_fixture_row(fixture_id="current-900")])
    request = H2HFeedRequest(home="Requested Hôme", away="Requested Away")
    now = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)

    resolved = resolve_fixture(lambda: session, request, now=now)

    assert resolved.resolved_by == "names_current_window"
    assert resolved.fixture_id == "current-900"
    assert session.calls == [
        {
            "window_start": datetime(2026, 8, 25, 12, 0, tzinfo=timezone.utc),
            "window_end": datetime(2026, 9, 10, 12, 0, tzinfo=timezone.utc),
        }
    ]


def test_as_of_is_not_mistaken_for_fixture_kickoff_date():
    session = _FakeSession(day_rows=[_fixture_row(fixture_id="current-900")])
    request = H2HFeedRequest(
        home="Requested Home",
        away="Requested Away",
        as_of="2020-01-01T00:00:00Z",
    )
    now = datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc)

    resolved = resolve_fixture(lambda: session, request, now=now)

    assert resolved.resolved_by == "names_current_window"
    assert session.calls[0]["window_start"] == datetime(
        2026, 8, 25, 12, 0, tzinfo=timezone.utc
    )


def test_names_without_date_fail_closed_when_current_window_is_ambiguous():
    session = _FakeSession(
        day_rows=[
            _fixture_row(fixture_id="current-a", provider_fixture_id="901"),
            _fixture_row(fixture_id="current-b", provider_fixture_id="902"),
        ]
    )
    request = H2HFeedRequest(home="Requested Home", away="Requested Away")

    with pytest.raises(AmbiguousLookup):
        resolve_fixture(
            lambda: session,
            request,
            now=datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc),
        )


def test_optional_league_disambiguates_current_window_exactly():
    other = _fixture_row(fixture_id="other-league", provider_fixture_id="901")
    other["league_name"] = "Other League"
    wanted = _fixture_row(fixture_id="wanted-league", provider_fixture_id="902")
    session = _FakeSession(day_rows=[other, wanted])
    request = H2HFeedRequest(
        home="Requested Home",
        away="Requested Away",
        league="test-league",
    )

    resolved = resolve_fixture(
        lambda: session,
        request,
        now=datetime(2026, 8, 27, 12, 0, tzinfo=timezone.utc),
    )

    assert resolved.fixture_id == "wanted-league"
    assert resolved.resolved_by == "names_current_window"
