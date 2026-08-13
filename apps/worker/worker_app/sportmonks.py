from dataclasses import dataclass
import asyncio, random
import httpx

from .resilience import CircuitBreaker

@dataclass(frozen=True)
class SportmonksPage:
    data: tuple[dict, ...]
    current_page: int
    last_page: int
    has_more: bool

class SportmonksClient:
    def __init__(
        self, *, api_token,
        base_url="https://api.sportmonks.com/v3/football",
        timeout_seconds=10.0,
        max_attempts=3,
        client=None,
        circuit_breaker=None,
    ):
        if not str(api_token).strip():
            raise ValueError("Sportmonks API token boş olamaz")
        self.api_token = str(api_token).strip()
        self.base_url = base_url.rstrip("/")
        self.max_attempts = max_attempts
        self.client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(timeout_seconds)
        )
        self._owns_client = client is None
        self.circuit_breaker = (
            circuit_breaker
            or CircuitBreaker(
                failure_threshold=5,
                recovery_timeout_seconds=30.0,
            )
        )

    async def close(self):
        if self._owns_client:
            await self.client.aclose()

    async def fixture_by_id(self, fixture_id, *, include=None):
        params = {"include": include} if include else {}
        payload = await self._request(
            "GET", f"/fixtures/{fixture_id}", params=params
        )
        return dict(payload.get("data") or {})

    async def events_by_fixture(self, fixture_id, *, page=1):
        payload = await self._request(
            "GET",
            f"/fixtures/{fixture_id}",
            params={"include": "events", "page": page},
        )
        fixture = dict(payload.get("data") or {})
        events = tuple(fixture.get("events") or ())
        pagination = (
            payload.get("pagination")
            or payload.get("meta", {}).get("pagination")
            or {}
        )
        current = int(pagination.get("current_page", page))
        last = int(pagination.get("last_page", current))
        return SportmonksPage(events, current, last, current < last)

    async def fixtures_between(
        self, start_date, end_date, *, include=None, page=1
    ):
        params = {"page": page}
        if include:
            params["include"] = include
        payload = await self._request(
            "GET",
            f"/fixtures/between/{start_date}/{end_date}",
            params=params,
        )
        pagination = (
            payload.get("pagination")
            or payload.get("meta", {}).get("pagination")
            or {}
        )
        current = int(pagination.get("current_page", page))
        last = int(pagination.get("last_page", current))
        return SportmonksPage(
            tuple(payload.get("data") or ()),
            current,
            last,
            current < last,
        )

    async def iter_fixtures_between(
        self, start_date, end_date, *, include=None, max_pages=100
    ):
        page = 1
        while page <= max_pages:
            result = await self.fixtures_between(
                start_date, end_date, include=include, page=page
            )
            for item in result.data:
                yield item
            if not result.has_more:
                break
            page += 1

    async def _request(self, method, path, *, params=None):
        self.circuit_breaker.before_call()
        query = dict(params or {})
        query["api_token"] = self.api_token
        last_error = None

        for attempt in range(self.max_attempts):
            try:
                response = await self.client.request(
                    method,
                    f"{self.base_url}{path}",
                    params=query,
                )
                if response.status_code == 429:
                    retry_after = float(
                        response.headers.get("Retry-After", "1")
                    )
                    await asyncio.sleep(min(retry_after, 5.0))
                    continue
                response.raise_for_status()
                payload = response.json()
                if not isinstance(payload, dict):
                    raise ValueError("Sportmonks yanıtı sözlük değil")
                self.circuit_breaker.record_success()
                return payload
            except (
                httpx.TimeoutException,
                httpx.NetworkError,
                httpx.HTTPStatusError,
            ) as exc:
                last_error = exc
                if attempt + 1 >= self.max_attempts:
                    break
                await asyncio.sleep(
                    min(
                        2.0,
                        0.25 * (2 ** attempt)
                        + random.random() * 0.05,
                    )
                )

        self.circuit_breaker.record_failure()
        raise RuntimeError(f"Sportmonks isteği başarısız: {last_error}")
