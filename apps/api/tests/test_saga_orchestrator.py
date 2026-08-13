import json
from apps.api.app.saga import RedisSagaRepository, SagaHandlerRegistry, SagaOrchestrator, SagaOwnershipLost

class Redis:
    def __init__(self): self.values = {}
    def setex(self, key, ttl, value): self.values[key] = value
    def get(self, key): return self.values.get(key)
    def eval(self, script, number_of_keys, *args):
        key, owner, payload = args[0], args[1], args[2]
        raw = self.values.get(key)
        if raw:
            current = json.loads(raw)
            if 'current.status' in script:
                if current['owner_token'] not in ('', owner): return [2, raw]
            elif current['owner_token'] != owner:
                return [2, raw]
        self.values[key] = payload
        return [1, payload]

def test_saga_completes_in_order():
    repo = RedisSagaRepository(Redis(), prefix='s')
    registry = SagaHandlerRegistry(); calls = []
    registry.register('a', lambda c: (calls.append('a') or {'x': 1}))
    registry.register('b', lambda c: (calls.append('b') or {'y': 2}))
    saga = repo.create(saga_type='t', step_names=('a', 'b'), now=1)
    out = SagaOrchestrator(repository=repo, registry=registry).run(saga.saga_id, owner_token='w')
    assert out.status == 'COMPLETED'
    assert calls == ['a', 'b']
    assert out.current_step == 2

def test_failure_compensates_reverse_order():
    repo = RedisSagaRepository(Redis(), prefix='s')
    registry = SagaHandlerRegistry(); calls = []
    registry.register('a', lambda c: {'a': 1}, lambda c, r: calls.append('undo-a'))
    registry.register('b', lambda c: {'b': 1}, lambda c, r: calls.append('undo-b'))
    registry.register('c', lambda c: (_ for _ in ()).throw(RuntimeError('boom')))
    saga = repo.create(saga_type='t', step_names=('a', 'b', 'c'))
    out = SagaOrchestrator(repository=repo, registry=registry).run(saga.saga_id, owner_token='w')
    assert out.status == 'COMPENSATED'
    assert calls == ['undo-b', 'undo-a']

def test_stale_owner_is_rejected():
    repo = RedisSagaRepository(Redis(), prefix='s')
    saga = repo.create(saga_type='t', step_names=('a',))
    repo.claim(saga.saga_id, owner_token='w1')
    try:
        repo.claim(saga.saga_id, owner_token='w2')
        assert False
    except SagaOwnershipLost:
        pass
