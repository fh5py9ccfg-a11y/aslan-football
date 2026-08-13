import pytest

from apps.api.app.feature_store import (
    FeatureDefinition,
    FeatureValidationError,
    FeatureValue,
    RedisFeatureStore,
)


class Redis:
    def __init__(self):
        self.values = {}
        self.sets = {}
        self.sorted_sets = {}

    def set(self, key, value):
        self.values[key] = value

    def setex(self, key, ttl, value):
        self.values[key] = value

    def get(self, key):
        return self.values.get(key)

    def sadd(self, key, value):
        self.sets.setdefault(key, set()).add(value)

    def smembers(self, key):
        return self.sets.get(key, set())

    def zadd(self, key, mapping):
        bucket = self.sorted_sets.setdefault(key, [])
        for value, score in mapping.items():
            bucket.append((float(score), value))
        bucket.sort(key=lambda item: item[0])

    def zremrangebyrank(self, key, start, stop):
        bucket = self.sorted_sets.get(key, [])
        if not bucket:
            return
        if stop < 0:
            stop = len(bucket) + stop
        if start < 0:
            start = len(bucket) + start
        if stop >= start:
            del bucket[start:stop + 1]

    def zrevrangebyscore(
        self,
        key,
        maximum,
        minimum,
        start=0,
        num=None,
    ):
        bucket = [
            value
            for score, value in reversed(
                self.sorted_sets.get(key, [])
            )
            if score <= float(maximum)
        ]
        if num is None:
            return bucket[start:]
        return bucket[start:start + num]


def definition():
    return FeatureDefinition(
        name="team_form",
        version="v1",
        entity_type="team",
        value_type="FLOAT",
        owner="ml-team",
        ttl_seconds=300,
        max_age_seconds=120,
        status="PRODUCTION",
        source="match-events",
        transformation="rolling-average-5",
        created_at=100,
        updated_at=100,
    )


def value(event_time=100, tenant_id="tenant-a"):
    return FeatureValue(
        tenant_id=tenant_id,
        entity_id="team-1",
        feature_name="team_form",
        feature_version="v1",
        value=0.75,
        event_time=event_time,
        ingested_at=event_time + 1,
        expires_at=event_time + 301,
        source="pipeline",
    )


def test_online_and_point_in_time_reads():
    store = RedisFeatureStore(
        Redis(),
        prefix="features",
    )
    store.register_definition(definition())
    store.put(value(event_time=100))
    store.put(value(event_time=200))

    online = store.get_online(
        tenant_id="tenant-a",
        entity_id="team-1",
        feature_name="team_form",
        feature_version="v1",
    )
    historical = store.get_as_of(
        tenant_id="tenant-a",
        entity_id="team-1",
        feature_name="team_form",
        feature_version="v1",
        as_of=150,
    )

    assert online.event_time == 200
    assert historical.event_time == 100


def test_tenant_isolation():
    store = RedisFeatureStore(
        Redis(),
        prefix="features",
    )
    store.register_definition(definition())
    store.put(value(tenant_id="tenant-a"))

    missing = store.get_online(
        tenant_id="tenant-b",
        entity_id="team-1",
        feature_name="team_form",
        feature_version="v1",
    )

    assert missing is None


def test_feature_type_validation():
    store = RedisFeatureStore(
        Redis(),
        prefix="features",
    )
    store.register_definition(definition())

    invalid = FeatureValue(
        **{
            **value().__dict__,
            "value": "not-a-number",
        }
    )

    with pytest.raises(FeatureValidationError):
        store.put(invalid)


def test_freshness_detection():
    store = RedisFeatureStore(
        Redis(),
        prefix="features",
    )
    store.register_definition(definition())
    store.put(value(event_time=100))

    freshness = store.freshness(
        tenant_id="tenant-a",
        entity_id="team-1",
        feature_name="team_form",
        feature_version="v1",
        now=250,
    )

    assert freshness.fresh is False
    assert freshness.age_seconds == 150
