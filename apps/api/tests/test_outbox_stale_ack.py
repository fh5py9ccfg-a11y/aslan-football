import json, pytest
from apps.api.app.compensation_outbox_publisher import OutboxDeliveryRecord, OutboxOwnershipLost, RedisOutboxDeliveryRepository
class Redis:
    def __init__(self): self.values={}
    def get(self,key): return self.values.get(key)
    def eval(self,script,n,*args):
        cur=json.loads(self.values[args[0]])
        if cur['owner_token']!=args[1]: return [2,self.values[args[0]]]
        return [1,args[2]]
def test_stale_ack_rejected():
    redis=Redis(); repo=RedisOutboxDeliveryRepository(redis,prefix='d')
    current=OutboxDeliveryRecord('e','IN_PROGRESS','b','tb',2,11,11,71,None,None,None)
    stale=OutboxDeliveryRecord('e','IN_PROGRESS','a','ta',1,0,0,60,None,None,None)
    redis.values['d:e']=json.dumps(current.__dict__)
    with pytest.raises(OutboxOwnershipLost): repo.mark_delivered(stale,now=20)
