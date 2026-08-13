from apps.api.app.session_maintenance import (
    RedisSessionIndexMaintainer,
)

class FakeRedis:
    def __init__(self):
        self.deleted = []

    def scan(self, cursor, match, count):
        return 0, []

    def smembers(self, key):
        return set()

    def ttl(self, key):
        return -1

    def delete(self, key):
        self.deleted.append(key)
        return 1

    def expire(self, key, ttl):
        return True

    def srem(self, key, value):
        return 0

def test_empty_index_is_deleted():
    redis = FakeRedis()
    maintainer = RedisSessionIndexMaintainer(
        redis
    )

    removed, repaired = maintainer._clean_index(
        "aslan:refresh:subject:empty"
    )

    assert removed == 0
    assert repaired == 0
    assert redis.deleted == [
        "aslan:refresh:subject:empty"
    ]
