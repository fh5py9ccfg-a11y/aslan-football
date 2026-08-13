from apps.api.app.model_deployment import (
    ModelDeploymentManager,
)
from apps.api.app.model_registry import (
    RedisModelRegistry,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def setex(self, key, ttl, value):
        self.values[key] = value

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


def register(registry, model_id):
    return registry.register(
        model_id=model_id,
        name=model_id,
        version="1.0.0",
        framework="sklearn",
        artifact_uri=f"s3://models/{model_id}",
        artifact_sha256="a" * 64,
        feature_version="features-v1",
        training_dataset="dataset-v1",
        now=100,
    )


def test_champion_challenger_promotion_and_rollback():
    redis = Redis()
    registry = RedisModelRegistry(
        redis,
        prefix="models",
    )
    register(registry, "m1")
    register(registry, "m2")

    manager = ModelDeploymentManager(
        redis,
        registry=registry,
        prefix="deploy",
    )

    first = manager.assign_champion(
        slot="match-winner",
        model_id="m1",
        now=101,
    )
    assert first.champion_model_id == "m1"

    challenger = manager.start_challenger(
        slot="match-winner",
        model_id="m2",
        rollout_percent=10,
        now=102,
    )
    assert challenger.challenger_model_id == "m2"

    promoted = manager.promote_challenger(
        slot="match-winner",
        now=103,
    )
    assert promoted.champion_model_id == "m2"

    rolled_back = manager.rollback(
        slot="match-winner",
        now=104,
    )
    assert rolled_back.champion_model_id == "m1"
