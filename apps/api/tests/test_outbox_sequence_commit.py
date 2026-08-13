import json
from dataclasses import dataclass
from apps.api.app.compensation_outbox import RedisCompensationCommitter
@dataclass
class C:
    compensation_id:str='c1'; request_id:str='r1'; claim_id:str='q1'; action:str='A'; status:str='PENDING'; reason:str=''; created_at:int=1; completed_at:int|None=None; attempts:int=0; next_attempt_at:int|None=1
@dataclass
class E:
    compensation_id:str='c1'; owner:str='w'; owner_token:str='token'; status:str='IN_PROGRESS'; claimed_at:int=1; heartbeat_at:int=1; lease_expires_at:int=61; attempts:int=1
class Redis:
    def __init__(self): self.values={}; self.counters={}
    def eval(self,script,n,*args):
        keys=args[:6]; argv=args[6:]; seqkey=keys[5]; self.counters[seqkey]=self.counters.get(seqkey,0)+1
        event=json.loads(argv[3]); event['sequence']=self.counters[seqkey]; payload=json.dumps(event); self.values[keys[2]]=payload; return [1,payload]
    def scan(self,cursor,match,count): return 0,[k for k in self.values if k.startswith('outbox:')]
    def get(self,k): return self.values.get(k)
def test_partition_sequence_is_monotonic():
    r=Redis(); c=RedisCompensationCommitter(r,compensation_prefix='comp',execution_prefix='exec',outbox_prefix='outbox',sequence_prefix='seq')
    a=c.commit_success(compensation=C('c1'),execution=E('c1'),result_payload={},now=1)
    b=c.commit_success(compensation=C('c2'),execution=E('c2'),result_payload={},now=2)
    assert (a.partition,a.sequence,b.sequence)==('r1',1,2)
