import sys, unittest, os
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.providers_v6 import (
    SportmonksConfig,
    HttpResponse,
    ProviderNotConnected,
    SportmonksClient,
    SportmonksNormalizer,
    ProviderConnectionInspector,
)
from aslan_ozaslan.admin.provider_connection_page import (
    render_provider_connection_page,
)

class FakeTransport:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def get(self, **kwargs):
        self.calls.append(kwargs)
        return self.responses.pop(0)

class SportmonksProviderTests(unittest.TestCase):
    def test_missing_token_blocks_request(self):
        transport = FakeTransport([])
        client = SportmonksClient(
            config=SportmonksConfig(api_token=None),
            transport=transport,
        )
        with self.assertRaises(ProviderNotConnected):
            client.inplay_livescores()
        self.assertEqual(transport.calls, [])

        status = ProviderConnectionInspector().inspect_sportmonks(
            SportmonksConfig(api_token=None)
        )
        self.assertFalse(status.request_allowed)
        self.assertEqual(status.label, "bağlantı bekliyor")

    def test_header_token_and_latest_live_endpoint(self):
        transport = FakeTransport([
            HttpResponse(200, {"data": [{"id": 12}]})
        ])
        client = SportmonksClient(
            config=SportmonksConfig(api_token="secret"),
            transport=transport,
        )
        result = client.latest_updated_livescores()
        self.assertEqual(result[0]["id"], 12)
        call = transport.calls[0]
        self.assertEqual(call["headers"]["Authorization"], "secret")
        self.assertTrue(call["url"].endswith("/livescores/latest"))

    def test_pagination_and_limit(self):
        transport = FakeTransport([
            HttpResponse(200, {
                "data": [{"id": 1}],
                "pagination": {"has_more": True},
            }),
            HttpResponse(200, {
                "data": [{"id": 2}],
                "pagination": {"has_more": False},
            }),
        ])
        client = SportmonksClient(
            config=SportmonksConfig(api_token="secret"),
            transport=transport,
        )
        result = client.fixtures_by_date("2026-07-31")
        self.assertEqual([item["id"] for item in result], [1, 2])
        self.assertEqual(len(transport.calls), 2)
        self.assertEqual(transport.calls[0]["params"]["per_page"], 50)

    def test_normalization_and_admin_page(self):
        normalized = SportmonksNormalizer().normalize_live_fixture({
            "id": 99,
            "minute": 71,
            "state": {"short_name": "LIVE"},
            "participants": [
                {"id": 1, "meta": {"location": "home"}},
                {"id": 2, "meta": {"location": "away"}},
            ],
            "scores": [
                {
                    "description": "CURRENT",
                    "participant": "home",
                    "score": {"goals": 2},
                },
                {
                    "description": "CURRENT",
                    "participant": "away",
                    "score": {"goals": 1},
                },
            ],
        })
        self.assertEqual(normalized.home_score, 2)
        self.assertEqual(normalized.away_score, 1)
        self.assertEqual(normalized.state, "LIVE")

        status = ProviderConnectionInspector().inspect_sportmonks(
            SportmonksConfig(api_token="secret")
        )
        page = render_provider_connection_page(status)
        self.assertIn("Veri Kaynağı Bağlantıları", page)
        self.assertIn("anahtar tanımlı", page)

if __name__ == "__main__":
    unittest.main()
