import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.broker_v6 import (
    InMemoryBroker,
    InboxOutboxRepository,
)
from aslan_ozaslan.broker_v6.schema_registry import (
    SchemaRegistry,
    SchemaDefinition,
    require_fields,
)
from aslan_ozaslan.broker_v6.retry import ExponentialRetryPolicy
from aslan_ozaslan.broker_v6.dead_letter import (
    DeadLetterReplayRepository,
    DeadLetterReplayer,
)
from aslan_ozaslan.broker_v6.health import BrokerHealthChecker
from aslan_ozaslan.broker_v6.config import KafkaConnectionConfig
from aslan_ozaslan.admin.broker_resilience_page import (
    render_broker_resilience_page,
)

class BrokerResilienceTests(unittest.TestCase):
    def test_schema_registry_validates_versions(self):
        registry = SchemaRegistry()
        registry.register(
            SchemaDefinition(
                "match-event",
                1,
                require_fields("event_id", "type", "team_id"),
            )
        )
        registry.validate(
            "match-event",
            1,
            {"event_id": "e1", "type": "GOAL", "team_id": "home"},
        )
        with self.assertRaises(ValueError):
            registry.validate("match-event", 1, {"event_id": "e2"})

    def test_retry_policy_exhausts(self):
        policy = ExponentialRetryPolicy(
            max_attempts=3,
            base_delay_seconds=2,
            max_delay_seconds=10,
        )
        first = policy.decide(0)
        second = policy.decide(1)
        exhausted = policy.decide(2)
        self.assertEqual(first.delay_seconds, 2)
        self.assertEqual(second.delay_seconds, 4)
        self.assertFalse(exhausted.should_retry)
        self.assertTrue(exhausted.exhausted)

    def test_dead_letter_replay(self):
        with tempfile.TemporaryDirectory() as temp:
            db = Path(temp) / "broker.db"
            repo = InboxOutboxRepository(db)
            broker = InMemoryBroker()
            broker.publish(
                topic="match-events",
                key="m1",
                value={"type": "BROKEN"},
            )
            message = broker.poll()[0]
            repo.begin(message)
            repo.fail(message, "invalid")

            replay_repo = DeadLetterReplayRepository(db)
            replayer = DeadLetterReplayer(
                repository=replay_repo,
                producer=broker,
            )
            count = replayer.replay()
            self.assertEqual(count, 1)
            replayed = broker.poll()
            self.assertEqual(replayed[0].topic, "match-events.retry")
            self.assertEqual(replayed[0].headers["x-replay"], "true")
            self.assertEqual(repo.counts()["dead_letter"], 0)

    def test_health_config_and_page(self):
        broker = InMemoryBroker()
        health = BrokerHealthChecker().check(broker)
        self.assertTrue(health.healthy)

        config = KafkaConnectionConfig(
            bootstrap_servers=("kafka:9092",),
            client_id="aslan-ozaslan",
            consumer_group="football-analytics",
        )
        config.validate()

        policy = ExponentialRetryPolicy(max_attempts=4)
        page = render_broker_resilience_page(
            health=health,
            retry_policy=policy,
            dead_letter_count=0,
            schema_count=1,
        )
        self.assertIn("Broker Resilience Center", page)
        self.assertIn("Broker sağlıklı", page)

if __name__ == "__main__":
    unittest.main()
