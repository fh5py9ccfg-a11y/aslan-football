import time

from apps.api.app.session_maintenance import (
    RedisSessionIndexMaintainer,
)

class EmptyRedis:
    def scan(self, cursor, match, count):
        return 0, []

def test_report_contains_duration():
    report = RedisSessionIndexMaintainer(
        EmptyRedis()
    ).run_once()

    assert report.duration_ms >= 0
    assert report.lease_acquired is True
