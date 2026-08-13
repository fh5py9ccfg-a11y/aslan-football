from __future__ import annotations
from dataclasses import dataclass
import json
import secrets
import time

from .compensation_execution import CompensationOwnershipLost

@dataclass(frozen=True)
class CompensationOutboxEvent:
    event_id: str
    partition: str
    sequence: int
    compensation_id: str
    request_id: str
    claim_id: str
    action: str
    status: str
    payload: dict
    created_at: int

class RedisCompensationCommitter:
    COMMIT_SCRIPT = """
    local compensation_key = KEYS[1]
    local execution_key = KEYS[2]
    local outbox_key = KEYS[3]
    local old_status_key = KEYS[4]
    local new_status_key = KEYS[5]
    local sequence_key = KEYS[6]

    local owner_token = ARGV[1]
    local compensation_payload = ARGV[2]
    local execution_payload = ARGV[3]
    local event_template = ARGV[4]
    local compensation_id = ARGV[5]
    local ttl = tonumber(ARGV[6])

    local execution_raw = redis.call('GET', execution_key)
    if not execution_raw then return {0, 'missing_execution'} end
    local execution = cjson.decode(execution_raw)
    if execution.owner_token ~= owner_token then return {2, execution_raw} end

    local sequence = redis.call('INCR', sequence_key)
    redis.call('EXPIRE', sequence_key, ttl)
    local event = cjson.decode(event_template)
    event.sequence = sequence
    local outbox_payload = cjson.encode(event)

    redis.call('SET', compensation_key, compensation_payload, 'EX', ttl)
    redis.call('SET', execution_key, execution_payload, 'EX', ttl)
    redis.call('SET', outbox_key, outbox_payload, 'EX', ttl)
    redis.call('SREM', old_status_key, compensation_id)
    redis.call('SADD', new_status_key, compensation_id)
    return {1, outbox_payload}
    """

    def __init__(self, client, *, compensation_prefix='aslan:compensation', execution_prefix='aslan:compensation-execution', outbox_prefix='aslan:compensation-outbox', sequence_prefix='aslan:compensation-outbox-sequence', ttl_seconds=2592000):
        self.client=client; self.compensation_prefix=compensation_prefix; self.execution_prefix=execution_prefix; self.outbox_prefix=outbox_prefix; self.sequence_prefix=sequence_prefix; self.ttl_seconds=ttl_seconds

    def commit_success(self, *, compensation, execution, result_payload, now=None):
        current=int(now if now is not None else time.time())
        partition=str(compensation.request_id)
        event_id=secrets.token_urlsafe(18)
        completed_compensation={**compensation.__dict__,'status':'COMPLETED','completed_at':current,'attempts':compensation.attempts+1,'next_attempt_at':None}
        completed_execution={**execution.__dict__,'status':'COMPLETED'}
        event_template={'event_id':event_id,'partition':partition,'sequence':0,'compensation_id':compensation.compensation_id,'request_id':compensation.request_id,'claim_id':compensation.claim_id,'action':compensation.action,'status':'COMPLETED','payload':dict(result_payload or {}),'created_at':current}
        result=self.client.eval(self.COMMIT_SCRIPT,6,
            f'{self.compensation_prefix}:record:{compensation.compensation_id}',
            f'{self.execution_prefix}:{compensation.compensation_id}',
            f'{self.outbox_prefix}:{event_id}',
            f'{self.compensation_prefix}:status:{compensation.status}',
            f'{self.compensation_prefix}:status:COMPLETED',
            f'{self.sequence_prefix}:{partition}',
            execution.owner_token,
            json.dumps(completed_compensation,ensure_ascii=False,separators=(',',':')),
            json.dumps(completed_execution,ensure_ascii=False,separators=(',',':')),
            json.dumps(event_template,ensure_ascii=False,separators=(',',':')),
            compensation.compensation_id,self.ttl_seconds)
        code=int(result[0])
        if code==0: raise KeyError('Compensation execution kaydı bulunamadı')
        if code==2: raise CompensationOwnershipLost('Stale compensation worker atomik commit yapamaz')
        payload=result[1].decode('utf-8') if isinstance(result[1],bytes) else result[1]
        return CompensationOutboxEvent(**json.loads(payload))

    def list_events(self, *, limit=100):
        cursor=0; items=[]
        while True:
            cursor,keys=self.client.scan(cursor=cursor,match=f'{self.outbox_prefix}:*',count=100)
            for key in keys:
                payload=self.client.get(key)
                if payload is None: continue
                if isinstance(payload,bytes): payload=payload.decode('utf-8')
                data=json.loads(payload)
                data.setdefault('partition',str(data.get('request_id','legacy')))
                data.setdefault('sequence',0)
                items.append(CompensationOutboxEvent(**data))
            if int(cursor)==0: break
        items.sort(key=lambda x:(x.partition,x.sequence,x.created_at,x.event_id))
        return tuple(items[:limit])
