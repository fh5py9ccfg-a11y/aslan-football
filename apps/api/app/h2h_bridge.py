"""Sportmonks H2H bridge for the Aslan Skor desktop client.

Contract: POST /h2h/feed with ``schema=aslan.h2h.v1``.

Resolution is deliberately conservative:

* an exact local/provider fixture id is tried first;
* only when that id is absent do exact-normalized home/away fields form the
  fallback lookup; date and league narrow it when supplied, otherwise a
  now-2-days through now+14-days window is searched;
* any ambiguous database match fails closed (HTTP 409);
* team ids must come from the stored Sportmonks participants payload.

The Sportmonks token is sent in the Authorization header, never in the URL,
and provider errors never echo request headers, URLs, or response bodies.
"""

from __future__ import annotations

import asyncio
import json
import os
import re
import time
import unicodedata
from collections import OrderedDict
from dataclasses import dataclass
from datetime import date, datetime, time as datetime_time, timedelta, timezone
from typing import Any, Awaitable, Callable, Literal

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator
from sqlalchemy import text
from starlette.concurrency import run_in_threadpool


SCHEMA_VERSION = "aslan.h2h.v1"
SPORTMONKS_BASE_URL = "https://api.sportmonks.com/v3/football"
SPORTMONKS_H2H_INCLUDE = "participants;scores;league;state"


class H2HFeedRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["aslan.h2h.v1"] = Field(
        default=SCHEMA_VERSION,
        alias="schema",
    )
    fixture_id: str | None = Field(default=None, min_length=1, max_length=160)
    home: str | None = Field(default=None, min_length=1, max_length=255)
    away: str | None = Field(default=None, min_length=1, max_length=255)
    kickoff_at: str | None = Field(default=None, min_length=8, max_length=64)
    # Request timestamp used by clients for freshness/audit. It is accepted for
    # compatibility but is not guessed to be the selected fixture's kickoff.
    as_of: str | None = Field(default=None, min_length=8, max_length=64)
    league: str | None = Field(default=None, min_length=1, max_length=255)
    limit: int = Field(default=8, ge=1, le=20)

    @model_validator(mode="after")
    def require_primary_or_team_names(self) -> "H2HFeedRequest":
        if self.fixture_id:
            return self
        if all((self.home, self.away)):
            return self
        raise ValueError("fixture_id veya home+away alanları gerekli")


class TeamRef(BaseModel):
    id: int
    name: str


class TargetFixtureOut(BaseModel):
    fixture_id: str
    provider_fixture_id: str
    league: str | None
    kickoff_at: str | None
    home: TeamRef
    away: TeamRef


class ScoreOut(BaseModel):
    requested_home: int
    requested_away: int
    score: str


class H2HMatchOut(BaseModel):
    fixture_id: str
    date: str
    kickoff_at: str
    league: str | None
    actual_home: TeamRef
    actual_away: TeamRef
    venue_orientation: Literal["same", "reversed"]
    regulation_time: Literal[True] = True
    ht: ScoreOut
    ft: ScoreOut
    result_from_requested_home: Literal["W", "D", "L"]


class H2HSummaryOut(BaseModel):
    requested_home_wins: int
    draws: int
    requested_away_wins: int
    avg_requested_home_goals: float
    avg_requested_away_goals: float


class CacheOut(BaseModel):
    hit: bool
    ttl_seconds: int


class H2HFeedResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_version: Literal["aslan.h2h.v1"] = Field(
        default=SCHEMA_VERSION,
        alias="schema",
    )
    source: Literal["sportmonks"] = "sportmonks"
    resolved_by: Literal["fixture_id", "names_date_league", "names_current_window"]
    orientation: Literal["requested_home_away"] = "requested_home_away"
    target_fixture: TargetFixtureOut
    cache: CacheOut
    count: int
    skipped_incomplete_scores: int
    summary: H2HSummaryOut
    matches: list[H2HMatchOut]


class LookupNotFound(Exception):
    pass


class AmbiguousLookup(Exception):
    pass


class UnusableFixture(Exception):
    pass


class ProviderUnavailable(Exception):
    pass


@dataclass(frozen=True)
class ResolvedFixture:
    resolved_by: Literal["fixture_id", "names_date_league", "names_current_window"]
    fixture_id: str
    provider_fixture_id: str
    league: str | None
    kickoff_at: datetime | None
    home_id: int
    home_name: str
    away_id: int
    away_name: str


_TRANSLITERATION = str.maketrans(
    {
        "ı": "i",
        "İ": "i",
        "ł": "l",
        "Ł": "l",
        "ø": "o",
        "Ø": "o",
        "đ": "d",
        "Đ": "d",
        "ß": "ss",
        "æ": "ae",
        "Æ": "ae",
        "œ": "oe",
        "Œ": "oe",
    }
)


def normalize_name(value: Any) -> str:
    """Normalize accents/case/punctuation without fuzzy or alias guessing."""
    translated = str(value or "").strip().translate(_TRANSLITERATION)
    decomposed = unicodedata.normalize("NFKD", translated).casefold()
    without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "", without_marks)


def _as_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _parse_iso_datetime(value: Any) -> datetime | None:
    if isinstance(value, datetime):
        return _as_utc(value)
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        return None
    return _as_utc(parsed)


def _lookup_day_bounds(value: str) -> tuple[datetime, datetime]:
    raw = str(value or "").strip()
    if not raw:
        raise UnusableFixture("kickoff_at geçerli bir ISO tarih/datetime olmalı")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        try:
            parsed_date = date.fromisoformat(raw)
        except ValueError as exc:
            raise UnusableFixture("kickoff_at geçerli bir ISO tarih/datetime olmalı") from exc
        start = datetime.combine(parsed_date, datetime_time.min, tzinfo=timezone.utc)
    else:
        parsed = _parse_iso_datetime(raw)
        if parsed is None:
            raise UnusableFixture("kickoff_at geçerli bir ISO tarih/datetime olmalı")
        start = datetime.combine(parsed.date(), datetime_time.min, tzinfo=timezone.utc)
    return start, start + timedelta(days=1)


def _json_object(raw_json: Any) -> dict[str, Any]:
    if isinstance(raw_json, dict):
        return raw_json
    try:
        payload = json.loads(raw_json or "{}")
    except (TypeError, ValueError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _positive_int(value: Any) -> int | None:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _unique_participant(
    participants: list[dict[str, Any]],
    *,
    location: str,
    fallback_name: str,
) -> dict[str, Any] | None:
    located = [
        item
        for item in participants
        if isinstance(item, dict)
        and str((item.get("meta") or {}).get("location") or "").casefold() == location
    ]
    if len(located) == 1:
        return located[0]
    if located:
        return None

    target = normalize_name(fallback_name)
    named = [
        item
        for item in participants
        if isinstance(item, dict) and normalize_name(item.get("name")) == target
    ]
    return named[0] if len(named) == 1 else None


def _resolved_from_row(
    row: dict[str, Any],
    *,
    resolved_by: Literal["fixture_id", "names_date_league", "names_current_window"],
) -> ResolvedFixture:
    raw = _json_object(row.get("raw_json"))
    participants = [
        item for item in (raw.get("participants") or []) if isinstance(item, dict)
    ]
    home = _unique_participant(
        participants,
        location="home",
        fallback_name=str(row.get("home_team") or ""),
    )
    away = _unique_participant(
        participants,
        location="away",
        fallback_name=str(row.get("away_team") or ""),
    )
    home_id = _positive_int((home or {}).get("id"))
    away_id = _positive_int((away or {}).get("id"))
    if home_id is None or away_id is None or home_id == away_id:
        raise UnusableFixture(
            "Sportmonks takım kimlikleri bu fikstürün participants verisinden doğrulanamadı"
        )

    return ResolvedFixture(
        resolved_by=resolved_by,
        fixture_id=str(row.get("fixture_id") or ""),
        provider_fixture_id=str(row.get("provider_fixture_id") or ""),
        league=str(row.get("league_name") or "").strip() or None,
        kickoff_at=_parse_iso_datetime(row.get("kickoff_at")),
        home_id=home_id,
        home_name=str((home or {}).get("name") or row.get("home_team") or "").strip(),
        away_id=away_id,
        away_name=str((away or {}).get("name") or row.get("away_team") or "").strip(),
    )


def _rows(result: Any) -> list[dict[str, Any]]:
    return [dict(item) for item in result.mappings().all()]


def resolve_fixture(
    session_factory: Callable[[], Any],
    request: H2HFeedRequest,
    *,
    now: datetime | None = None,
) -> ResolvedFixture:
    """Resolve target fixture without fuzzy guesses or silent tie-breaking."""
    with session_factory() as session:
        if request.fixture_id:
            exact = _rows(
                session.execute(
                    text(
                        """
                        SELECT fixture_id, provider_fixture_id, league_name,
                               home_team, away_team, kickoff_at, raw_json
                        FROM fixtures
                        WHERE provider = 'sportmonks'
                          AND (fixture_id = :fixture_id
                               OR provider_fixture_id = :fixture_id)
                        LIMIT 3
                        """
                    ),
                    {"fixture_id": request.fixture_id},
                )
            )
            if len(exact) > 1:
                raise AmbiguousLookup("fixture_id birden fazla Sportmonks kaydıyla eşleşti")
            if len(exact) == 1:
                return _resolved_from_row(exact[0], resolved_by="fixture_id")

        if not all((request.home, request.away)):
            raise LookupNotFound("Fikstür bulunamadı; home+away alanları da verilmedi")

        requested_kickoff = request.kickoff_at
        if requested_kickoff:
            window_start, window_end = _lookup_day_bounds(str(requested_kickoff))
            resolved_by: Literal["names_date_league", "names_current_window"] = (
                "names_date_league"
            )
        else:
            current = _as_utc(now or datetime.now(timezone.utc))
            assert current is not None
            window_start = current - timedelta(days=2)
            window_end = current + timedelta(days=14)
            resolved_by = "names_current_window"

        candidates = _rows(
            session.execute(
                text(
                    """
                    SELECT fixture_id, provider_fixture_id, league_name,
                           home_team, away_team, kickoff_at, raw_json
                    FROM fixtures
                    WHERE provider = 'sportmonks'
                      AND kickoff_at >= :window_start
                      AND kickoff_at < :window_end
                    ORDER BY kickoff_at ASC
                    LIMIT 5000
                    """
                ),
                {"window_start": window_start, "window_end": window_end},
            )
        )

    wanted_home = normalize_name(request.home)
    wanted_away = normalize_name(request.away)
    wanted_league = normalize_name(request.league) if request.league else ""
    exact_fallback = [
        row
        for row in candidates
        if normalize_name(row.get("home_team")) == wanted_home
        and normalize_name(row.get("away_team")) == wanted_away
        and (
            not wanted_league
            or normalize_name(row.get("league_name")) == wanted_league
        )
    ]
    if not exact_fallback:
        if resolved_by == "names_current_window":
            raise LookupNotFound(
                "Adlarla güncel Sportmonks penceresinde kesin bir fikstür bulunamadı"
            )
        raise LookupNotFound("Ad+tarih alanlarıyla kesin bir Sportmonks fikstürü bulunamadı")
    if len(exact_fallback) > 1:
        scope = "güncel pencere" if resolved_by == "names_current_window" else "tarih"
        raise AmbiguousLookup(
            f"Ad+{scope} alanları birden fazla fikstürle eşleşti; fixture_id gerekli"
        )
    return _resolved_from_row(exact_fallback[0], resolved_by=resolved_by)


class TTLCache:
    """Small process-local cache; avoids repeat provider quota use per worker."""

    def __init__(self, ttl_seconds: int = 21600, max_items: int = 256):
        self.ttl_seconds = max(60, int(ttl_seconds))
        self.max_items = max(1, int(max_items))
        self._items: OrderedDict[str, tuple[float, tuple[dict[str, Any], ...]]] = OrderedDict()
        self._lock = asyncio.Lock()

    async def get_or_fetch(
        self,
        key: str,
        fetcher: Callable[[], Awaitable[list[dict[str, Any]]]],
    ) -> tuple[list[dict[str, Any]], bool]:
        async with self._lock:
            now = time.monotonic()
            cached = self._items.get(key)
            if cached and cached[0] > now:
                self._items.move_to_end(key)
                return list(cached[1]), True
            if cached:
                self._items.pop(key, None)

            value = await fetcher()
            self._items[key] = (now + self.ttl_seconds, tuple(value))
            self._items.move_to_end(key)
            while len(self._items) > self.max_items:
                self._items.popitem(last=False)
            return list(value), False


def _bounded_env_float(name: str, default: float, *, minimum: float, maximum: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except (TypeError, ValueError):
        value = default
    return max(minimum, min(maximum, value))


class SportmonksH2HClient:
    def __init__(
        self,
        *,
        api_token: str,
        client: httpx.AsyncClient | None = None,
        base_url: str = SPORTMONKS_BASE_URL,
    ):
        token = str(api_token or "").strip()
        if not token:
            raise ValueError("Sportmonks API token boş olamaz")
        self._token = token
        self._base_url = base_url.rstrip("/")
        self._client = client

    async def fetch(self, first_team_id: int, second_team_id: int) -> list[dict[str, Any]]:
        first = _positive_int(first_team_id)
        second = _positive_int(second_team_id)
        if first is None or second is None or first == second:
            raise ProviderUnavailable("Sportmonks H2H takım kimlikleri geçersiz")

        timeout = httpx.Timeout(
            connect=_bounded_env_float(
                "H2H_CONNECT_TIMEOUT_SECONDS", 3.0, minimum=0.5, maximum=10.0
            ),
            read=_bounded_env_float(
                "H2H_READ_TIMEOUT_SECONDS", 8.0, minimum=1.0, maximum=20.0
            ),
            write=5.0,
            pool=3.0,
        )
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=timeout)
        try:
            response = await client.get(
                f"{self._base_url}/fixtures/head-to-head/{first}/{second}",
                params={"include": SPORTMONKS_H2H_INCLUDE},
                # Header auth prevents the secret appearing in URLs/access logs.
                headers={"Authorization": self._token, "Accept": "application/json"},
                timeout=timeout,
            )
            if response.status_code != 200:
                raise ProviderUnavailable(
                    f"Sportmonks H2H yanıt vermedi (HTTP {response.status_code})"
                )
            try:
                payload = response.json()
            except ValueError as exc:
                raise ProviderUnavailable("Sportmonks H2H geçersiz JSON döndürdü") from exc
            data = payload.get("data") if isinstance(payload, dict) else None
            if not isinstance(data, list):
                raise ProviderUnavailable("Sportmonks H2H veri biçimi geçersiz")
            return [item for item in data if isinstance(item, dict)]
        except httpx.TimeoutException as exc:
            raise ProviderUnavailable("Sportmonks H2H isteği zaman aşımına uğradı") from exc
        except httpx.NetworkError as exc:
            raise ProviderUnavailable("Sportmonks H2H ağına erişilemedi") from exc
        finally:
            if owns_client:
                await client.aclose()


def _participant_pair(fixture: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]] | None:
    participants = [
        item for item in (fixture.get("participants") or []) if isinstance(item, dict)
    ]
    home = [
        item
        for item in participants
        if str((item.get("meta") or {}).get("location") or "").casefold() == "home"
    ]
    away = [
        item
        for item in participants
        if str((item.get("meta") or {}).get("location") or "").casefold() == "away"
    ]
    if len(home) != 1 or len(away) != 1:
        return None
    return home[0], away[0]


def _score_pair(
    scores: Any,
    description: str,
    *,
    actual_home_id: int,
    actual_away_id: int,
) -> tuple[int, int] | None:
    found: dict[str, int] = {}
    for item in scores or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("description") or "").upper() != description:
            continue
        score = item.get("score") or {}
        try:
            goals = int(score.get("goals"))
        except (TypeError, ValueError):
            continue
        if goals < 0:
            continue
        side = str(score.get("participant") or "").casefold()
        participant_id = _positive_int(item.get("participant_id"))
        if side not in {"home", "away"}:
            if participant_id == actual_home_id:
                side = "home"
            elif participant_id == actual_away_id:
                side = "away"
            else:
                continue
        previous = found.get(side)
        if previous is not None and previous != goals:
            return None
        found[side] = goals
    if set(found) != {"home", "away"}:
        return None
    return found["home"], found["away"]


def normalize_h2h_matches(
    fixtures: list[dict[str, Any]],
    target: ResolvedFixture,
    *,
    limit: int,
) -> tuple[list[dict[str, Any]], int]:
    """Return HT and provable regulation-FT scores in requested-team orientation.

    ``2ND_HALF`` is the Sportmonks end-of-regulation score. ``CURRENT`` is not
    accepted as a fallback because it cannot prove that extra-time/shootout
    state was excluded.
    """
    normalized: list[tuple[datetime, dict[str, Any]]] = []
    skipped = 0
    cutoff = target.kickoff_at

    for fixture in fixtures:
        kickoff = _parse_iso_datetime(fixture.get("starting_at"))
        if kickoff is None or (cutoff is not None and kickoff >= cutoff):
            skipped += 1
            continue
        pair = _participant_pair(fixture)
        if pair is None:
            skipped += 1
            continue
        actual_home, actual_away = pair
        actual_home_id = _positive_int(actual_home.get("id"))
        actual_away_id = _positive_int(actual_away.get("id"))
        if actual_home_id is None or actual_away_id is None:
            skipped += 1
            continue

        if (actual_home_id, actual_away_id) == (target.home_id, target.away_id):
            orientation = "same"
        elif (actual_home_id, actual_away_id) == (target.away_id, target.home_id):
            orientation = "reversed"
        else:
            skipped += 1
            continue

        ht_actual = _score_pair(
            fixture.get("scores"),
            "1ST_HALF",
            actual_home_id=actual_home_id,
            actual_away_id=actual_away_id,
        )
        regulation_ft_actual = _score_pair(
            fixture.get("scores"),
            "2ND_HALF",
            actual_home_id=actual_home_id,
            actual_away_id=actual_away_id,
        )
        if ht_actual is None or regulation_ft_actual is None:
            skipped += 1
            continue

        if orientation == "same":
            ht_home, ht_away = ht_actual
            ft_home, ft_away = regulation_ft_actual
        else:
            ht_away, ht_home = ht_actual
            ft_away, ft_home = regulation_ft_actual

        result = "W" if ft_home > ft_away else "L" if ft_home < ft_away else "D"
        league = fixture.get("league") or {}
        item = {
            "fixture_id": str(fixture.get("id") or ""),
            "date": kickoff.date().isoformat(),
            "kickoff_at": kickoff.isoformat(),
            "league": (
                str(league.get("name") or "").strip() or None
                if isinstance(league, dict)
                else None
            ),
            "actual_home": {
                "id": actual_home_id,
                "name": str(actual_home.get("name") or "").strip(),
            },
            "actual_away": {
                "id": actual_away_id,
                "name": str(actual_away.get("name") or "").strip(),
            },
            "venue_orientation": orientation,
            "regulation_time": True,
            "ht": {
                "requested_home": ht_home,
                "requested_away": ht_away,
                "score": f"{ht_home}-{ht_away}",
            },
            "ft": {
                "requested_home": ft_home,
                "requested_away": ft_away,
                "score": f"{ft_home}-{ft_away}",
            },
            "result_from_requested_home": result,
        }
        normalized.append((kickoff, item))

    normalized.sort(key=lambda pair: pair[0], reverse=True)
    return [item for _, item in normalized[: max(1, min(20, int(limit)))]], skipped


def summarize(matches: list[dict[str, Any]]) -> dict[str, Any]:
    count = len(matches)
    wins = sum(item["result_from_requested_home"] == "W" for item in matches)
    draws = sum(item["result_from_requested_home"] == "D" for item in matches)
    losses = sum(item["result_from_requested_home"] == "L" for item in matches)
    home_goals = sum(int(item["ft"]["requested_home"]) for item in matches)
    away_goals = sum(int(item["ft"]["requested_away"]) for item in matches)
    return {
        "requested_home_wins": wins,
        "draws": draws,
        "requested_away_wins": losses,
        "avg_requested_home_goals": round(home_goals / count, 2) if count else 0.0,
        "avg_requested_away_goals": round(away_goals / count, 2) if count else 0.0,
    }


def _cache_ttl_seconds() -> int:
    try:
        value = int(os.getenv("H2H_CACHE_TTL_SECONDS", "21600"))
    except ValueError:
        value = 21600
    return max(60, min(86400, value))


_H2H_CACHE = TTLCache(ttl_seconds=_cache_ttl_seconds())


def _session_factory() -> Callable[[], Any]:
    from .db import SessionLocal

    return SessionLocal


def _sportmonks_token() -> str:
    # Use the existing Settings object so Render's SPORTMONKS_API_TOKEN remains
    # the single source of truth. Never include this value in a response/log.
    from .settings import settings

    return str(settings.sportmonks_api_token or "").strip()


router = APIRouter(tags=["h2h"])


@router.post("/h2h/feed", response_model=H2HFeedResponse)
async def h2h_feed(request: H2HFeedRequest) -> dict[str, Any]:
    try:
        target = await run_in_threadpool(resolve_fixture, _session_factory(), request)
    except LookupNotFound as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except AmbiguousLookup as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except UnusableFixture as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    token = _sportmonks_token()
    if not token:
        raise HTTPException(status_code=503, detail="Sportmonks sunucu bağlantısı yapılandırılmamış")

    first, second = sorted((target.home_id, target.away_id))
    cache_key = f"sportmonks:h2h:{first}:{second}:{SPORTMONKS_H2H_INCLUDE}"

    async def fetcher() -> list[dict[str, Any]]:
        return await SportmonksH2HClient(api_token=token).fetch(first, second)

    try:
        raw_fixtures, cache_hit = await _H2H_CACHE.get_or_fetch(cache_key, fetcher)
    except ProviderUnavailable as exc:
        # ProviderUnavailable messages are intentionally pre-sanitized.
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    matches, skipped = normalize_h2h_matches(
        raw_fixtures,
        target,
        limit=request.limit,
    )
    return {
        "schema": SCHEMA_VERSION,
        "source": "sportmonks",
        "resolved_by": target.resolved_by,
        "orientation": "requested_home_away",
        "target_fixture": {
            "fixture_id": target.fixture_id,
            "provider_fixture_id": target.provider_fixture_id,
            "league": target.league,
            "kickoff_at": target.kickoff_at.isoformat() if target.kickoff_at else None,
            "home": {"id": target.home_id, "name": target.home_name},
            "away": {"id": target.away_id, "name": target.away_name},
        },
        "cache": {"hit": cache_hit, "ttl_seconds": _H2H_CACHE.ttl_seconds},
        "count": len(matches),
        "skipped_incomplete_scores": skipped,
        "summary": summarize(matches),
        "matches": matches,
    }
