from __future__ import annotations
from dataclasses import dataclass
import json

@dataclass(frozen=True)
class EventSequenceState:
    partition: str
    last_sequence: int
    last_event_id: str

class OutOfOrderEvent(ValueError):
    pass

class DuplicateSequence(ValueError):
    pass

class RedisEventOrderingRepository:
    ADVANCE_SCRIPT = """
    local key = KEYS[1]
    local sequence = tonumber(ARGV[1])
    local event_id = ARGV[2]
    local partition = ARGV[3]
    local ttl = tonumber(ARGV[4])

    local raw = redis.call('GET', key)
    if raw then
        local current = cjson.decode(raw)
        local last = tonumber(current.last_sequence or 0)
        if sequence == last then
            if current.last_event_id == event_id then
                return {2, raw}
            end
            return {-2, raw}
        end
        if sequence < last then
            return {-1, raw}
        end
        if sequence > last + 1 then
            return {-3, raw}
        end
    elseif sequence ~= 1 then
        return {-3, 'missing_origin'}
    end

    local payload = cjson.encode({
        partition=partition,
        last_sequence=sequence,
        last_event_id=event_id
    })
    redis.call('SET', key, payload, 'EX', ttl)
    return {1, payload}
    """

    def __init__(self, client, *, prefix='aslan:event-ordering', ttl_seconds=2592000):
        if ttl_seconds <= 0:
            raise ValueError('ordering ttl pozitif olmalıdır')
        self.client=client; self.prefix=prefix; self.ttl_seconds=ttl_seconds

    def advance(self, *, partition:str, sequence:int, event_id:str):
        result=self.client.eval(self.ADVANCE_SCRIPT,1,self._key(partition),sequence,event_id,partition,self.ttl_seconds)
        code=int(result[0])
        if code == -1: raise OutOfOrderEvent('Event sequence geriye gidemez')
        if code == -2: raise DuplicateSequence('Aynı sequence farklı event tarafından kullanılıyor')
        if code == -3: raise OutOfOrderEvent('Event sequence boşluk içeriyor')
        return code == 1, self._deserialize(result[1])

    def get(self, partition:str):
        payload=self.client.get(self._key(partition))
        return None if payload is None else self._deserialize(payload)

    def _key(self, partition): return f'{self.prefix}:{partition}'
    @staticmethod
    def _deserialize(payload):
        if isinstance(payload,bytes): payload=payload.decode('utf-8')
        data=json.loads(payload)
        return EventSequenceState(partition=str(data['partition']),last_sequence=int(data['last_sequence']),last_event_id=str(data['last_event_id']))
