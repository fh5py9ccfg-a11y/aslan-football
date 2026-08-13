from apps.api.app.session_maintenance import (
    RedisSessionIndexMaintainer,
)

class FakeRedis:
    def __init__(self):
        self.sets = {
            "aslan:refresh:subject:user-1": {
                "live-1",
                "orphan-1",
            },
            "aslan:refresh:family:family-1": {
                "live-1",
                "orphan-1",
            },
        }
        self.ttls = {
            "aslan:refresh:session:live-1": 120,
            "aslan:refresh:session:orphan-1": -2,
            "aslan:refresh:subject:user-1": 10,
            "aslan:refresh:family:family-1": -1,
        }
        self.deleted = set()

    def scan(self, cursor, match, count):
        if "subject" in match:
            return 0, [
                "aslan:refresh:subject:user-1"
            ]
        return 0, [
            "aslan:refresh:family:family-1"
        ]

    def smembers(self, key):
        return set(self.sets.get(key, set()))

    def ttl(self, key):
        return self.ttls.get(key, -2)

    def srem(self, key, value):
        self.sets[key].discard(value)
        return 1

    def expire(self, key, ttl):
        self.ttls[key] = ttl
        return True

    def delete(self, key):
        self.deleted.add(key)
        return 1

def test_orphan_cleanup_and_ttl_repair():
    redis = FakeRedis()
    maintainer = RedisSessionIndexMaintainer(
        redis
    )

    report = maintainer.run_once()

    assert report.subject_indexes_scanned == 1
    assert report.family_indexes_scanned == 1
    assert report.orphan_members_removed == 2
    assert report.ttl_repairs == 2
    assert "orphan-1" not in redis.sets[
        "aslan:refresh:subject:user-1"
    ]
    assert redis.ttls[
        "aslan:refresh:family:family-1"
    ] == 120
