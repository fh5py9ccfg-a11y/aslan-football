import asyncio, time
from apps.api.app.outbox_delivery_heartbeat import OutboxPublishGuard
class Record: event_id='e1'
class Repo:
    def __init__(self): self.calls=0
    def heartbeat(self, record): self.calls+=1; return record
def test_guard_renews_lease():
    repo=Repo(); guard=OutboxPublishGuard(repository=repo, heartbeat_interval_seconds=0.01)
    result=asyncio.run(guard.run(record=Record(), operation=lambda: time.sleep(0.04) or 'ok'))
    assert result.receipt=='ok' and repo.calls>=2
