import json
from apps.api.app.compensation_outbox_publisher import RedisOutboxDeliveryRepository
class Redis:
    def __init__(self): self.values={}
    def get(self,key): return self.values.get(key)
    def eval(self,script,n,*args):
        key=args[0]; now=int(args[1]); payload=args[2]; raw=self.values.get(key)
        if raw:
            cur=json.loads(raw)
            if cur['status']=='IN_PROGRESS' and cur['lease_expires_at']>now: return [0,raw]
        self.values[key]=payload; return [1,payload]
def test_takeover_after_expiry():
    repo=RedisOutboxDeliveryRepository(Redis(), prefix='d', lease_seconds=10)
    assert repo.claim(event_id='e',owner='a',now=0)[0]
    assert not repo.claim(event_id='e',owner='b',now=5)[0]
    created, rec=repo.claim(event_id='e',owner='b',now=11)
    assert created and rec.owner=='b' and rec.attempts==2
