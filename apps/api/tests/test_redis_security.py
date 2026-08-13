from apps.api.app.redis_security import (
    RedisRevocationRepository,
    RedisWebSocketTicketRepository,
)

class FakeRedis:
    def __init__(self):
        self.values = {}

    def setex(self, key, ttl, value):
        self.values[key] = value
        return True

    def exists(self, key):
        return int(key in self.values)

    def eval(self, script, number_of_keys, key):
        value = self.values.get(key)
        if value is None:
            return None
        self.values.pop(key, None)
        return value

def test_redis_ticket_atomic_single_use():
    redis = FakeRedis()
    repository = RedisWebSocketTicketRepository(redis)
    ticket = repository.issue(
        subject="u1",
        roles=("viewer",),
    )

    assert repository.consume(ticket.ticket) is not None
    assert repository.consume(ticket.ticket) is None

def test_redis_revocation_repository():
    redis = FakeRedis()
    repository = RedisRevocationRepository(redis)
    repository.revoke("token-1", 9999999999)
    assert repository.is_revoked("token-1") is True
