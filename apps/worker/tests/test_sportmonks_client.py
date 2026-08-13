import asyncio
import httpx
from worker_app.sportmonks import SportmonksClient
from worker_app.provider_sync import SportmonksFixtureSyncService

def test_fixture_by_id_and_pagination():
    requests = []
    async def handler(request):
        requests.append(request)
        page = int(request.url.params.get("page", "1"))
        if "/fixtures/" in request.url.path and "/between/" not in request.url.path:
            return httpx.Response(200, json={"data": {"id": 10}})
        return httpx.Response(200, json={
            "data": [{"id": page}],
            "pagination": {"current_page": page, "last_page": 2},
        })
    async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = SportmonksClient(
        api_token="token", base_url="https://example.test", client=async_client
    )
    assert asyncio.run(client.fixture_by_id(10))["id"] == 10
    async def collect():
        return [item async for item in client.iter_fixtures_between(
            "2026-08-01", "2026-08-02"
        )]
    assert [item["id"] for item in asyncio.run(collect())] == [1, 2]
    assert all(r.url.params["api_token"] == "token" for r in requests)
    asyncio.run(async_client.aclose())

def test_retry_on_server_error():
    attempts = {"count": 0}
    async def handler(request):
        attempts["count"] += 1
        if attempts["count"] < 2:
            return httpx.Response(500, json={"error": "temporary"})
        return httpx.Response(200, json={"data": {"id": 11}})
    async_client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    client = SportmonksClient(
        api_token="token", base_url="https://example.test",
        max_attempts=2, client=async_client
    )
    assert asyncio.run(client.fixture_by_id(11))["id"] == 11
    assert attempts["count"] == 2
    asyncio.run(async_client.aclose())

def test_fixture_sync_service():
    class FakeClient:
        async def iter_fixtures_between(self, *args, **kwargs):
            yield {"id": 1}
            yield {"id": 2}
    class FakePublisher:
        def __init__(self): self.items = []
        async def publish(self, topic, payload, message_id):
            self.items.append((topic, payload, message_id))
    publisher = FakePublisher()
    service = SportmonksFixtureSyncService(
        client=FakeClient(), publisher=publisher
    )
    report = asyncio.run(service.sync_between(
        start_date="2026-08-01", end_date="2026-08-02"
    ))
    assert (report.fetched, report.published, report.failed) == (2, 2, 0)
