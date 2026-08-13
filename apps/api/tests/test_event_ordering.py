import json
import pytest
from apps.api.app.event_ordering import RedisEventOrderingRepository, OutOfOrderEvent, DuplicateSequence
class Redis:
    def __init__(self): self.values={}
    def get(self,k): return self.values.get(k)
    def eval(self,script,n,*args):
        key,seq,event,partition=args[:4]; seq=int(seq); raw=self.values.get(key)
        if raw:
            cur=json.loads(raw); last=cur['last_sequence']
            if seq==last: return [2,raw] if cur['last_event_id']==event else [-2,raw]
            if seq<last:return [-1,raw]
            if seq>last+1:return [-3,raw]
        elif seq!=1:return [-3,'missing_origin']
        payload=json.dumps({'partition':partition,'last_sequence':seq,'last_event_id':event}); self.values[key]=payload; return [1,payload]
def test_monotonic_and_replay():
    repo=RedisEventOrderingRepository(Redis(),prefix='ordering')
    created,state=repo.advance(partition='p1',sequence=1,event_id='e1'); assert created and state.last_sequence==1
    created,_=repo.advance(partition='p1',sequence=1,event_id='e1'); assert created is False
    repo.advance(partition='p1',sequence=2,event_id='e2')
def test_gap_and_duplicate_rejected():
    repo=RedisEventOrderingRepository(Redis(),prefix='ordering')
    with pytest.raises(OutOfOrderEvent): repo.advance(partition='p1',sequence=2,event_id='e2')
    repo.advance(partition='p1',sequence=1,event_id='e1')
    with pytest.raises(DuplicateSequence): repo.advance(partition='p1',sequence=1,event_id='other')
