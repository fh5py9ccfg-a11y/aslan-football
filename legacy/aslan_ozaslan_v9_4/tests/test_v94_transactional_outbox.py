import sys, unittest, tempfile
from pathlib import Path
from datetime import datetime, timedelta, timezone
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.distributed_v9 import (
    SQLiteTransactionalOutbox,
    OutboxLeaseManager,
    OutboxPublisher,
    RetryPolicy,
    OutboxStateRepository,
    OutboxWorker,
    IngestionOutboxTransaction,
)
from aslan_ozaslan.admin.outbox_operations_page import (
    render_outbox_operations_page,
)

class TransactionalOutboxTests(unittest.TestCase):
    def test_transaction_enqueues_once(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = SQLiteTransactionalOutbox(
                Path(temp) / "outbox.db"
            )
            transaction = IngestionOutboxTransaction(outbox)
            payload = {"id": 1, "fixture_id": 10}

            first = transaction.archive_and_enqueue(
                archive_table="provider_archive",
                provider="sportmonks",
                payload_type="event",
                external_id="1",
                payload_hash="hash-1",
                payload=payload,
                message_id="msg-1",
                topic="provider.events",
            )
            second = transaction.archive_and_enqueue(
                archive_table="provider_archive",
                provider="sportmonks",
                payload_type="event",
                external_id="1",
                payload_hash="hash-1",
                payload=payload,
                message_id="msg-1-copy",
                topic="provider.events",
            )

            self.assertTrue(first)
            self.assertFalse(second)
            self.assertEqual(
                len(outbox.list_by_status("PENDING")),
                1,
            )

    def test_two_workers_do_not_claim_same_message(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = SQLiteTransactionalOutbox(
                Path(temp) / "outbox.db"
            )
            outbox.enqueue(
                message_id="m1",
                aggregate_id="a1",
                topic="events",
                payload={"x": 1},
            )
            leases = OutboxLeaseManager(outbox)
            now = datetime.now(timezone.utc)

            first = leases.claim(
                worker_id="worker-1",
                limit=1,
                lease_seconds=30,
                now=now,
            )
            second = leases.claim(
                worker_id="worker-2",
                limit=1,
                lease_seconds=30,
                now=now,
            )

            self.assertEqual(len(first), 1)
            self.assertEqual(len(second), 0)

    def test_worker_publish_retry_dead_letter_and_page(self):
        with tempfile.TemporaryDirectory() as temp:
            outbox = SQLiteTransactionalOutbox(
                Path(temp) / "outbox.db"
            )
            outbox.enqueue(
                message_id="ok",
                aggregate_id="a1",
                topic="events",
                payload={"mode": "ok"},
            )
            outbox.enqueue(
                message_id="retry",
                aggregate_id="a2",
                topic="events",
                payload={"mode": "fail"},
            )

            def publish_callable(*, topic, payload, message_id):
                if payload["mode"] == "fail":
                    raise RuntimeError("broker_down")

            worker = OutboxWorker(
                worker_id="worker-1",
                lease_manager=OutboxLeaseManager(outbox),
                publisher=OutboxPublisher(publish_callable),
                state_repository=OutboxStateRepository(outbox),
                retry_policy=RetryPolicy(
                    max_attempts=2,
                    base_delay_seconds=1,
                    max_delay_seconds=1,
                ),
            )

            report = worker.run_once(limit=10)
            self.assertEqual(report.published, 1)
            self.assertEqual(report.retried, 1)
            self.assertEqual(
                len(outbox.list_by_status("PUBLISHED")),
                1,
            )
            self.assertEqual(
                len(outbox.list_by_status("RETRY")),
                1,
            )

            retry_message = outbox.get("retry")
            with outbox._connect() as connection:
                connection.execute(
                    '''
                    UPDATE outbox_messages
                    SET available_at=?, attempt_count=1
                    WHERE message_id='retry'
                    ''',
                    (
                        (
                            datetime.now(timezone.utc)
                            - timedelta(seconds=1)
                        ).isoformat(),
                    ),
                )

            second = worker.run_once(limit=10)
            self.assertEqual(second.dead_lettered, 1)
            self.assertEqual(
                len(outbox.list_by_status("DEAD_LETTER")),
                1,
            )

            page = render_outbox_operations_page(outbox, second)
            self.assertIn("Transactional Outbox Operations", page)
            self.assertIn("Dead letter", page)

if __name__ == "__main__":
    unittest.main()
