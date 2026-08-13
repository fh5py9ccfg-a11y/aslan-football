from apps.api.app.refresh_sessions import (
    RedisRefreshSessionRepository,
)

class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.commands = []

    def setex(self, key, ttl, value):
        self.commands.append(
            ("setex", key, value)
        )
        return self

    def sadd(self, key, value):
        self.commands.append(
            ("sadd", key, value)
        )
        return self

    def expire(self, key, ttl):
        self.commands.append(
            ("expire", key, ttl)
        )
        return self

    def execute(self):
        for command in self.commands:
            if command[0] == "setex":
                self.redis.values[
                    command[1]
                ] = command[2]
            elif command[0] == "sadd":
                self.redis.sets.setdefault(
                    command[1],
                    set(),
                ).add(command[2])
        return [True] * len(self.commands)

class FakeRedis:
    def __init__(self):
        self.values = {}
        self.sets = {}

    def pipeline(self):
        return FakePipeline(self)

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value):
        self.values[key] = value

    def smembers(self, key):
        return self.sets.get(key, set())

def test_redis_refresh_issue_and_list():
    redis = FakeRedis()
    repository = RedisRefreshSessionRepository(
        redis
    )

    _, session = repository.issue(
        subject="user-1",
        roles=("viewer",),
        ttl_seconds=100,
    )

    loaded = repository.get(
        session.session_id
    )
    listed = repository.list_subject(
        "user-1"
    )

    assert loaded is not None
    assert loaded.subject == "user-1"
    assert len(listed) == 1
