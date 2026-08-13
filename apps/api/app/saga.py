from __future__ import annotations
from dataclasses import dataclass
import json
import secrets
import time

@dataclass(frozen=True)
class SagaStep:
    name: str
    status: str
    attempts: int = 0
    result: dict | None = None
    error: str | None = None

@dataclass(frozen=True)
class SagaRecord:
    saga_id: str
    saga_type: str
    status: str
    owner_token: str
    created_at: int
    updated_at: int
    current_step: int
    steps: tuple[SagaStep, ...]
    context: dict

class SagaOwnershipLost(RuntimeError):
    pass

class RedisSagaRepository:
    CLAIM_SCRIPT = """
    local key = KEYS[1]
    local owner = ARGV[1]
    local payload = ARGV[2]
    local ttl = tonumber(ARGV[3])
    local raw = redis.call('GET', key)
    if raw then
      local current = cjson.decode(raw)
      if current.status == 'COMPLETED' or current.status == 'COMPENSATED' then
        return {0, raw}
      end
      if current.owner_token ~= '' and current.owner_token ~= owner then
        return {2, raw}
      end
    end
    redis.call('SET', key, payload, 'EX', ttl)
    return {1, payload}
    """
    UPDATE_SCRIPT = """
    local key = KEYS[1]
    local owner = ARGV[1]
    local payload = ARGV[2]
    local ttl = tonumber(ARGV[3])
    local raw = redis.call('GET', key)
    if not raw then return {0, 'missing'} end
    local current = cjson.decode(raw)
    if current.owner_token ~= owner then return {2, raw} end
    redis.call('SET', key, payload, 'EX', ttl)
    return {1, payload}
    """
    def __init__(self, client, *, prefix='aslan:saga', ttl_seconds=2592000):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def create(self, *, saga_type, step_names, context=None, now=None):
        current = int(now if now is not None else time.time())
        item = SagaRecord(
            saga_id=secrets.token_urlsafe(18),
            saga_type=saga_type,
            status='PENDING',
            owner_token='',
            created_at=current,
            updated_at=current,
            current_step=0,
            steps=tuple(SagaStep(name=n, status='PENDING') for n in step_names),
            context=dict(context or {}),
        )
        self.client.setex(self._key(item.saga_id), self.ttl_seconds, self._dump(item))
        return item

    def claim(self, saga_id, *, owner_token=None, now=None):
        item = self.get(saga_id)
        if item is None:
            raise KeyError('Saga bulunamadı')
        token = owner_token or secrets.token_urlsafe(18)
        current = int(now if now is not None else time.time())
        claimed = SagaRecord(**{**item.__dict__, 'owner_token': token, 'status': 'RUNNING', 'updated_at': current})
        result = self.client.eval(self.CLAIM_SCRIPT, 1, self._key(saga_id), token, self._dump(claimed), self.ttl_seconds)
        if int(result[0]) == 2:
            raise SagaOwnershipLost('Saga başka worker tarafından sahiplenildi')
        return int(result[0]) == 1, self._load(result[1])

    def save(self, item):
        result = self.client.eval(self.UPDATE_SCRIPT, 1, self._key(item.saga_id), item.owner_token, self._dump(item), self.ttl_seconds)
        if int(result[0]) == 0:
            raise KeyError('Saga bulunamadı')
        if int(result[0]) == 2:
            raise SagaOwnershipLost('Stale saga worker güncelleme yapamaz')
        return item

    def get(self, saga_id):
        raw = self.client.get(self._key(saga_id))
        return None if raw is None else self._load(raw)

    def _key(self, saga_id):
        return f'{self.prefix}:{saga_id}'

    @staticmethod
    def _dump(item):
        data = dict(item.__dict__)
        data['steps'] = [dict(step.__dict__) for step in item.steps]
        return json.dumps(data, ensure_ascii=False, separators=(',', ':'))

    @staticmethod
    def _load(raw):
        if isinstance(raw, bytes):
            raw = raw.decode('utf-8')
        data = json.loads(raw)
        data['steps'] = tuple(SagaStep(**step) for step in data['steps'])
        return SagaRecord(**data)

class SagaHandlerRegistry:
    def __init__(self):
        self.handlers = {}
        self.compensators = {}

    def register(self, name, handler, compensator=None):
        self.handlers[name] = handler
        self.compensators[name] = compensator

    def handler(self, name):
        if name not in self.handlers:
            raise KeyError(f'Saga handler bulunamadı: {name}')
        return self.handlers[name]

    def compensator(self, name):
        return self.compensators.get(name)

class SagaOrchestrator:
    def __init__(self, *, repository, registry):
        self.repository = repository
        self.registry = registry

    def run(self, saga_id, *, owner_token=None, now=None):
        _, saga = self.repository.claim(saga_id, owner_token=owner_token, now=now)
        steps = list(saga.steps)
        completed = [i for i, step in enumerate(steps[:saga.current_step]) if step.status == 'COMPLETED']
        for i in range(saga.current_step, len(steps)):
            step = steps[i]
            try:
                result = self.registry.handler(step.name)(dict(saga.context)) or {}
                steps[i] = SagaStep(step.name, 'COMPLETED', step.attempts + 1, dict(result), None)
                completed.append(i)
                saga = SagaRecord(**{**saga.__dict__, 'steps': tuple(steps), 'current_step': i + 1, 'updated_at': int(time.time())})
                self.repository.save(saga)
            except Exception as exc:
                steps[i] = SagaStep(step.name, 'FAILED', step.attempts + 1, None, str(exc))
                saga = SagaRecord(**{**saga.__dict__, 'steps': tuple(steps), 'status': 'COMPENSATING', 'updated_at': int(time.time())})
                self.repository.save(saga)
                return self._compensate(saga, completed)
        saga = SagaRecord(**{**saga.__dict__, 'status': 'COMPLETED', 'steps': tuple(steps), 'updated_at': int(time.time())})
        return self.repository.save(saga)

    def _compensate(self, saga, completed):
        steps = list(saga.steps)
        errors = []
        for i in reversed(completed):
            compensator = self.registry.compensator(steps[i].name)
            if compensator is None:
                continue
            try:
                compensator(dict(saga.context), steps[i].result or {})
                steps[i] = SagaStep(steps[i].name, 'COMPENSATED', steps[i].attempts, steps[i].result, None)
            except Exception as exc:
                errors.append(str(exc))
        status = 'COMPENSATION_FAILED' if errors else 'COMPENSATED'
        saga = SagaRecord(**{**saga.__dict__, 'status': status, 'steps': tuple(steps), 'updated_at': int(time.time())})
        return self.repository.save(saga)
