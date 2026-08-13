import json
from apps.api.app.saga import RedisSagaRepository, SagaHandlerRegistry, SagaOrchestrator, SagaRecord, SagaStep

class Redis:
    def __init__(self): self.values = {}
    def setex(self, key, ttl, value): self.values[key] = value
    def get(self, key): return self.values.get(key)
    def eval(self, script, number_of_keys, *args):
        self.values[args[0]] = args[2]
        return [1, args[2]]

def test_resume_skips_completed_step():
    repo = RedisSagaRepository(Redis(), prefix='s')
    calls = []; registry = SagaHandlerRegistry()
    registry.register('a', lambda c: (calls.append('a') or {}))
    registry.register('b', lambda c: (calls.append('b') or {}))
    saga = repo.create(saga_type='t', step_names=('a', 'b'))
    resumed = SagaRecord(**{**saga.__dict__, 'steps': (SagaStep('a', 'COMPLETED', 1, {}, None), SagaStep('b', 'PENDING')), 'current_step': 1})
    repo.client.values[repo._key(saga.saga_id)] = repo._dump(resumed)
    out = SagaOrchestrator(repository=repo, registry=registry).run(saga.saga_id, owner_token='w2')
    assert calls == ['b']
    assert out.status == 'COMPLETED'
