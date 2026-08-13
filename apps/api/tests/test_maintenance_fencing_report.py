from apps.api.app.distributed_lease import StaleFencingToken
from apps.api.app.session_maintenance import RedisSessionIndexMaintainer

class Redis:
    def scan(self, cursor, match, count):
        return 0, ["index"]

    def smembers(self, key):
        return {"orphan"}

    def ttl(self, key):
        return -2

class Mutator:
    fencing_token = 7

    def remove_orphan(self, index_key, session_id):
        raise StaleFencingToken("stale")

def test_stale_write_marks_aborted_report():
    report = RedisSessionIndexMaintainer(
        Redis(),
        mutator=Mutator(),
    ).run_once()

    assert report.aborted is True
    assert report.lease_lost is True
    assert report.stale_write_rejected is True
    assert report.fencing_token == 7
