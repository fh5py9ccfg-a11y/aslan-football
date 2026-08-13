import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.provider_gateway_v9 import (
    SportmonksPayloadSchemaValidator,
    SportmonksPayloadNormalizer,
    PayloadQuarantineRepository,
    SportmonksPayloadGateway,
)
from aslan_ozaslan.admin.provider_gateway_page import (
    render_provider_gateway_page,
)

class ProviderPayloadGatewayTests(unittest.TestCase):
    def fixture_payload(self):
        return {
            "id": 100,
            "league_id": 8,
            "season_id": 22000,
            "starting_at": "2026-08-01T18:00:00+00:00",
            "state": {
                "developer_name": "INPLAY",
                "minute": 65,
            },
            "participants": [
                {"id": 1, "meta": {"location": "home"}},
                {"id": 2, "meta": {"location": "away"}},
            ],
            "scores": [
                {"participant_id": 1, "score": {"goals": 2}},
                {"participant_id": 2, "score": {"goals": 1}},
            ],
        }

    def player_payload(self):
        return {
            "id": 501,
            "display_name": "Oyuncu",
            "team_id": 1,
            "position_id": 8,
            "nationality_id": 190,
            "date_of_birth": "2002-05-10",
        }

    def event_payload(self):
        return {
            "id": 9001,
            "fixture_id": 100,
            "participant_id": 1,
            "player_id": 501,
            "minute": 65,
            "extra_minute": None,
            "type": {"developer_name": "goal"},
            "cancelled": False,
        }

    def test_valid_payloads_are_normalized(self):
        with tempfile.TemporaryDirectory() as temp:
            gateway = SportmonksPayloadGateway(
                validator=SportmonksPayloadSchemaValidator(),
                normalizer=SportmonksPayloadNormalizer(),
                quarantine_repository=PayloadQuarantineRepository(
                    Path(temp) / "quarantine.json"
                ),
            )

            fixture = gateway.process_fixture(self.fixture_payload())
            player = gateway.process_player(self.player_payload())
            event = gateway.process_event(self.event_payload())

            self.assertTrue(fixture.accepted)
            self.assertEqual(fixture.normalized.home_score, 2)
            self.assertEqual(fixture.normalized.away_score, 1)

            self.assertTrue(player.accepted)
            self.assertEqual(player.normalized.name, "Oyuncu")

            self.assertTrue(event.accepted)
            self.assertEqual(event.normalized.event_type, "GOAL")

    def test_invalid_payload_is_quarantined(self):
        with tempfile.TemporaryDirectory() as temp:
            quarantine = PayloadQuarantineRepository(
                Path(temp) / "quarantine.json"
            )
            gateway = SportmonksPayloadGateway(
                validator=SportmonksPayloadSchemaValidator(),
                normalizer=SportmonksPayloadNormalizer(),
                quarantine_repository=quarantine,
            )

            result = gateway.process_event({
                "fixture_id": 100,
                "minute": 999,
            })

            self.assertFalse(result.accepted)
            self.assertIn("event_id_missing", result.errors)
            self.assertIn("event_minute_invalid", result.errors)
            self.assertEqual(len(quarantine.list_all()), 1)

    def test_admin_page(self):
        with tempfile.TemporaryDirectory() as temp:
            quarantine = PayloadQuarantineRepository(
                Path(temp) / "quarantine.json"
            )
            gateway = SportmonksPayloadGateway(
                validator=SportmonksPayloadSchemaValidator(),
                normalizer=SportmonksPayloadNormalizer(),
                quarantine_repository=quarantine,
            )

            results = (
                gateway.process_fixture(self.fixture_payload()),
                gateway.process_player(self.player_payload()),
                gateway.process_event(self.event_payload()),
            )
            page = render_provider_gateway_page(
                results,
                len(quarantine.list_all()),
            )
            self.assertIn("Sportmonks Provider Payload Gateway", page)
            self.assertIn("Karantina kayıtları", page)

if __name__ == "__main__":
    unittest.main()
