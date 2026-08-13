import json

from apps.api.app.refresh_sessions import (
    RedisRefreshSessionRepository,
)

class FakePipeline:
    def __init__(self, redis):
        self.redis = redis
        self.commands = []

    def setex(self, key, ttl, value):
        self.commands.append(("setex", key, value))
        return self

    def sadd(self, key, value):
        self.commands.append(("sadd", key, value))
        return self

    def expire(self, key, ttl):
        self.commands.append(("expire", key, ttl))
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

    def eval(
        self,
        script,
        number_of_keys,
        index_key,
        session_prefix,
    ):
        count = 0
        for session_id in self.sets.get(
            index_key,
            set(),
        ):
            key = session_prefix + session_id
            raw = self.values.get(key)
            if raw is None:
                continue
            data = json.loads(raw)
            if data["status"] == "ACTIVE":
                data["status"] = "REVOKED"
                self.values[key] = json.dumps(
                    data,
                    separators=(",", ":"),
                )
                count += 1
        return count

def test_redis_family_and_subject_indexes():
    redis = FakeRedis()
    repo = RedisRefreshSessionRepository(redis)

    _, session = repo.issue(
        subject="user-x",
        roles=("viewer",),
        ttl_seconds=100,
    )

    assert session.session_id in redis.sets[
        repo._subject_key("user-x")
    ]
    assert session.session_id in redis.sets[
        repo._family_key(session.family_id)
    ]

    assert repo.revoke_subject("user-x") == 1
    assert repo.get(session.session_id).status == "REVOKED"
