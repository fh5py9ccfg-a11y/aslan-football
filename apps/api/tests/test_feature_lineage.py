from apps.api.app.feature_store import (
    FeatureDefinition,
    FeatureLineageService,
    RedisFeatureStore,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def set(self, key, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())


def test_feature_lineage_description():
    store = RedisFeatureStore(
        Redis(),
        prefix="features",
    )
    store.register_definition(
        FeatureDefinition(
            name="xg_delta",
            version="v2",
            entity_type="team",
            value_type="FLOAT",
            owner="analytics",
            ttl_seconds=60,
            max_age_seconds=30,
            status="PRODUCTION",
            source="shots",
            transformation="home-xg-away-xg",
            created_at=100,
            updated_at=100,
        )
    )

    lineage = FeatureLineageService(
        store=store
    ).describe(
        feature_name="xg_delta",
        feature_version="v2",
    )

    assert lineage["source"] == "shots"
    assert lineage["owner"] == "analytics"
