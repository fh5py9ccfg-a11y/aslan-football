import time

from apps.api.app.session_maintenance import (
    RedisSessionIndexMaintainer,
)

class SlowRedis:
    def scan(self, cursor, match, count):
        return 0, ["index-1", "index-2"]

    def smembers(self, key):
        time.sleep(0.01)
        return set()

    def ttl(self, key):
        return -2

    def delete(self, key):
        return 1

def test_time_budget_stops_run():
    report = RedisSessionIndexMaintainer(
        SlowRedis(),
        max_indexes_per_run=100,
        time_budget_seconds=0.005,
    ).run_once()

    assert report.budget_exhausted is True
