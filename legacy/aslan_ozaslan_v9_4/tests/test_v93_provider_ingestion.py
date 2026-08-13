import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.provider_gateway_v9 import (
    SportmonksPayloadSchemaValidator,
    SportmonksPayloadNormalizer,
    PayloadQuarantineRepository,
    SportmonksPayloadGateway,
)
from aslan_ozaslan.ingestion_v9 import (
    PayloadFingerprint,
    SQLiteIngestionLedger,
    ProviderRawArchive,
    IngestionCheckpointRepository,
    ProviderEventProjector,
    ProviderIngestionOrchestrator,
    ProviderPagedSyncService,
)
from aslan_ozaslan.event_sourcing_v6 import SQLiteEventStore
from aslan_ozaslan.admin.provider_ingestion_page import (
    render_provider_ingestion_page,
)

class ProviderIngestionTests(unittest.TestCase):
    def event_payload(self, event_id=9001, minute=65):
        return {
            "id": event_id,
            "fixture_id": 100,
            "participant_id": 1,
            "player_id": 501,
            "minute": minute,
            "extra_minute": None,
            "type": {"developer_name": "goal"},
            "cancelled": False,
        }

    def build(self, temp):
        quarantine = PayloadQuarantineRepository(
            Path(temp) / "quarantine.json"
        )
        gateway = SportmonksPayloadGateway(
            validator=SportmonksPayloadSchemaValidator(),
            normalizer=SportmonksPayloadNormalizer(),
            quarantine_repository=quarantine,
        )
        event_store = SQLiteEventStore(Path(temp) / "events.db")
        archive = ProviderRawArchive(Path(temp) / "archive.json")
        orchestrator = ProviderIngestionOrchestrator(
            gateway=gateway,
            ledger=SQLiteIngestionLedger(Path(temp) / "ledger.db"),
            archive=archive,
            fingerprint=PayloadFingerprint(),
            event_projector=ProviderEventProjector(event_store),
        )
        return orchestrator, quarantine, event_store, archive

    def test_ingestion_is_idempotent_and_projects_event(self):
        with tempfile.TemporaryDirectory() as temp:
            orchestrator, quarantine, event_store, archive = self.build(temp)

            first = orchestrator.ingest(
                payload_type="event",
                payload=self.event_payload(),
            )
            second = orchestrator.ingest(
                payload_type="event",
                payload=self.event_payload(),
            )

            self.assertTrue(first.accepted)
            self.assertTrue(first.archived)
            self.assertTrue(first.projected)
            self.assertTrue(second.duplicate)
            self.assertFalse(second.projected)
            self.assertEqual(archive.count(), 1)
            self.assertEqual(len(event_store.stream("100")), 1)
            self.assertEqual(len(quarantine.list_all()), 0)

    def test_invalid_event_is_quarantined(self):
        with tempfile.TemporaryDirectory() as temp:
            orchestrator, quarantine, _, archive = self.build(temp)
            result = orchestrator.ingest(
                payload_type="event",
                payload={"fixture_id": 100, "minute": 999},
            )
            self.assertFalse(result.accepted)
            self.assertTrue(result.quarantined)
            self.assertEqual(archive.count(), 0)
            self.assertEqual(len(quarantine.list_all()), 1)

    def test_batch_sync_checkpoint_and_page(self):
        with tempfile.TemporaryDirectory() as temp:
            orchestrator, _, _, archive = self.build(temp)
            checkpoints = IngestionCheckpointRepository(
                Path(temp) / "checkpoint.json"
            )
            sync = ProviderPagedSyncService(
                orchestrator=orchestrator,
                checkpoint_repository=checkpoints,
            )
            pages = [
                [self.event_payload(9001, 65)],
                [self.event_payload(9002, 70)],
            ]
            reports = sync.sync_pages(
                stream_name="live-events",
                payload_type="event",
                pages=pages,
            )
            self.assertEqual(len(reports), 2)
            checkpoint = checkpoints.load("live-events")
            self.assertEqual(checkpoint["cursor"], "END")
            self.assertEqual(checkpoint["processed_count"], 2)

            batch = orchestrator.ingest_batch(
                payload_type="event",
                payloads=[self.event_payload(9003, 75)],
            )
            page = render_provider_ingestion_page(
                batch,
                archive.count(),
            )
            self.assertIn("Provider Ingestion Orchestrator", page)
            self.assertIn("Arşiv kayıtları", page)

if __name__ == "__main__":
    unittest.main()
