import pytest

from apps.api.app.model_registry import (
    ModelRegistryConflict,
    RedisModelRegistry,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def get(self, key):
        return self.values.get(key)

    def setex(self, key, ttl, value):
        self.values[key] = value

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


def test_model_registration_and_listing():
    registry = RedisModelRegistry(
        Redis(),
        prefix="models",
    )
    model = registry.register(
        model_id="m1",
        name="winner-model",
        version="1.0.0",
        framework="sklearn",
        artifact_uri="s3://models/m1",
        artifact_sha256="a" * 64,
        feature_version="features-v1",
        training_dataset="dataset-v1",
        now=100,
    )

    assert model.status == "REGISTERED"
    assert registry.list_models()[0].model_id == "m1"


def test_duplicate_model_id_is_rejected():
    registry = RedisModelRegistry(
        Redis(),
        prefix="models",
    )
    kwargs = dict(
        model_id="m1",
        name="winner-model",
        version="1.0.0",
        framework="sklearn",
        artifact_uri="s3://models/m1",
        artifact_sha256="a" * 64,
        feature_version="features-v1",
        training_dataset="dataset-v1",
        now=100,
    )
    registry.register(**kwargs)

    with pytest.raises(ModelRegistryConflict):
        registry.register(**kwargs)
