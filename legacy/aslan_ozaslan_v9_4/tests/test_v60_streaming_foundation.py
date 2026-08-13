import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.streaming_v6 import (
    StreamEnvelope,
    JsonCheckpointRepository,
    OrderedEventBuffer,
    EventLedger,
    ResilientStreamProcessor,
    StreamRecoveryPlanner,
)
from aslan_ozaslan.admin.streaming_control_page import (
    render_streaming_control_page,
)

class StreamingFoundationTests(unittest.TestCase):
    def envelope(self, sequence, event_id, kind="EVENT", payload=None):
        return StreamEnvelope(
            stream_id="match-1",
            sequence=sequence,
            event_id=event_id,
            payload_type=kind,
            payload=payload or {"type": "SHOT"},
            occurred_at=1000.0 + sequence,
        )

    def test_out_of_order_events_are_buffered(self):
        buffer = OrderedEventBuffer(expected_sequence=0)
        self.assertEqual(buffer.push(self.envelope(1, "e1")), ())
        ready = buffer.push(self.envelope(0, "e0"))
        self.assertEqual([item.sequence for item in ready], [0, 1])
        self.assertEqual(buffer.pending_count(), 0)

    def test_ledger_supports_corrections(self):
        ledger = EventLedger()
        first = ledger.apply_event("e1", {"type": "GOAL", "team": "home"})
        second = ledger.apply_correction(
            "e1",
            {"type": "NO_GOAL", "team": "home"},
            active=False,
        )
        self.assertEqual(first.version, 1)
        self.assertEqual(second.version, 2)
        self.assertFalse(second.active)

    def test_processor_checkpoint_and_recovery(self):
        with tempfile.TemporaryDirectory() as temp:
            repo = JsonCheckpointRepository(Path(temp) / "checkpoint.json")
            processor = ResilientStreamProcessor(
                stream_id="match-1",
                checkpoint_repository=repo,
            )

            pending = processor.process(self.envelope(1, "e1"))
            self.assertEqual(pending.applied_sequences, ())
            applied = processor.process(self.envelope(0, "e0"))
            self.assertEqual(applied.applied_sequences, (0, 1))
            self.assertEqual(applied.checkpoint.last_sequence, 1)
            self.assertEqual(applied.checkpoint.processed_events, 2)

            correction = self.envelope(
                2,
                "c1",
                "CORRECTION",
                {
                    "target_event_id": "e1",
                    "replacement": {"type": "SHOT_ON_TARGET"},
                    "active": True,
                },
            )
            corrected = processor.process(correction)
            self.assertEqual(corrected.checkpoint.corrected_events, 1)
            self.assertEqual(processor.ledger.get("e1").version, 2)

            reloaded = repo.load("match-1")
            plan = StreamRecoveryPlanner().build(
                checkpoint=reloaded,
                provider_high_watermark=5,
            )
            self.assertTrue(plan.replay_required)
            self.assertEqual(plan.resume_from_sequence, 3)

            page = render_streaming_control_page(
                reloaded,
                plan,
                processor.ledger.active_events(),
            )
            self.assertIn("Streaming Control Center", page)
            self.assertIn("Son sequence", page)

if __name__ == "__main__":
    unittest.main()
