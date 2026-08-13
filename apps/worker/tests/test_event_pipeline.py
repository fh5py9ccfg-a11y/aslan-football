import asyncio
import tempfile
from pathlib import Path
import httpx

from worker_app.checkpoint import JsonCheckpointRepository
from worker_app.event_sync import SportmonksEventSyncService
from worker_app.provider_event_bridge import ProviderEventToApiBridge
from worker_app.consumer import ConsumedMessage

class FakePublisher:
    def __init__(self):
        self.items = []

    async def publish(self, topic, payload, message_id):
        self.items.append((topic, payload, message_id))

class FakeClient:
    async def events_by_fixture(self, fixture_id, page=1):
        from worker_app.sportmonks import SportmonksPage
        return SportmonksPage(
            data=(
                {"id": 10, "fixture_id": fixture_id},
                {"id": 11, "fixture_id": fixture_id},
            ),
            current_page=1,
            last_page=1,
            has_more=False,
        )

def test_event_sync_checkpoint_and_skip():
    with tempfile.TemporaryDirectory() as temp:
        checkpoints = JsonCheckpointRepository(
            Path(temp) / "checkpoints.json"
        )
        publisher = FakePublisher()
        service = SportmonksEventSyncService(
            client=FakeClient(),
            publisher=publisher,
            checkpoints=checkpoints,
        )

        first = asyncio.run(service.sync_fixture("100"))
        second = asyncio.run(service.sync_fixture("100"))

        assert first.published == 2
        assert second.skipped == 2
        assert len(publisher.items) == 2

def test_provider_event_bridge_posts_api_event():
    captured = {}

    async def handler(request):
        captured["url"] = str(request.url)
        captured["json"] = request.content.decode()
        captured["correlation"] = request.headers["X-Correlation-ID"]
        return httpx.Response(200, json={"ok": True})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler)
    )
    bridge = ProviderEventToApiBridge(
        api_base_url="https://api.test",
        client=client,
    )
    message = ConsumedMessage(
        stream="provider.events",
        stream_id="1-0",
        message_id="sportmonks:event:99",
        payload={
            "id": 99,
            "fixture_id": 100,
            "minute": 12,
            "sort_order": 1,
            "team": "HOME",
            "type": {"developer_name": "goal"},
        },
    )
    asyncio.run(bridge.handle(message))

    assert captured["url"].endswith("/fixtures/100/events")
    assert captured["correlation"] == "sportmonks:event:99"
    assert '"event_type":"GOAL"' in captured["json"]
    asyncio.run(client.aclose())
