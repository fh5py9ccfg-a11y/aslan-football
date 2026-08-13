from dataclasses import dataclass
import secrets

@dataclass(frozen=True)
class LeaseState:
    acquired: bool
    owner_id: str
    expires_in_seconds: int
    fencing_token: int = 0

class LeaseLost(RuntimeError):
    pass

class StaleFencingToken(RuntimeError):
    pass

class RedisLease:
    ACQUIRE_SCRIPT = '''
    if redis.call("EXISTS", KEYS[1]) == 1 then
        return {0, 0}
    end
    local token = redis.call("INCR", KEYS[2])
    redis.call("SET", KEYS[1], ARGV[1] .. ":" .. token, "EX", ARGV[2])
    return {1, token}
    '''

    RELEASE_SCRIPT = '''
    if redis.call("GET", KEYS[1]) == ARGV[1] .. ":" .. ARGV[2] then
        return redis.call("DEL", KEYS[1])
    end
    return 0
    '''

    RENEW_SCRIPT = '''
    if redis.call("GET", KEYS[1]) == ARGV[1] .. ":" .. ARGV[2] then
        return redis.call("EXPIRE", KEYS[1], ARGV[3])
    end
    return 0
    '''

    def __init__(
        self,
        client,
        *,
        key,
        ttl_seconds=60,
        owner_id=None,
        counter_key=None,
    ):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds pozitif olmalıdır")
        self.client = client
        self.key = key
        self.counter_key = counter_key or f"{key}:fencing-counter"
        self.ttl_seconds = ttl_seconds
        self.owner_id = owner_id or secrets.token_urlsafe(16)
        self.fencing_token = 0

    def acquire(self):
        result = self.client.eval(
            self.ACQUIRE_SCRIPT,
            2,
            self.key,
            self.counter_key,
            self.owner_id,
            self.ttl_seconds,
        )

        if isinstance(result, (list, tuple)):
            acquired = int(result[0]) == 1
            if acquired:
                self.fencing_token = int(result[1])
            return acquired

        # Backward-compatible fallback for lightweight fake clients.
        acquired = bool(
            self.client.set(
                self.key,
                self.owner_id,
                nx=True,
                ex=self.ttl_seconds,
            )
        )
        if acquired:
            incr = getattr(self.client, "incr", None)
            self.fencing_token = (
                int(incr(self.counter_key))
                if callable(incr)
                else 1
            )
        return acquired

    def renew(self):
        if self.fencing_token <= 0:
            # Compatibility with pre-fencing test doubles.
            return bool(
                self.client.eval(
                    self.RENEW_SCRIPT,
                    1,
                    self.key,
                    self.owner_id,
                    self.ttl_seconds,
                )
            )
        return bool(
            self.client.eval(
                self.RENEW_SCRIPT,
                1,
                self.key,
                self.owner_id,
                self.fencing_token,
                self.ttl_seconds,
            )
        )

    def assert_owned(self):
        if not self.renew():
            raise LeaseLost("Dağıtık lease kaybedildi")

    def release(self):
        if self.fencing_token <= 0:
            return bool(
                self.client.eval(
                    self.RELEASE_SCRIPT,
                    1,
                    self.key,
                    self.owner_id,
                )
            )
        released = bool(
            self.client.eval(
                self.RELEASE_SCRIPT,
                1,
                self.key,
                self.owner_id,
                self.fencing_token,
            )
        )
        if released:
            self.fencing_token = 0
        return released

    def state(self):
        value = self.client.get(self.key)
        ttl = int(self.client.ttl(self.key))
        if isinstance(value, bytes):
            value = value.decode()

        owner = str(value or "")
        token = 0
        if ":" in owner:
            owner, _, raw_token = owner.rpartition(":")
            try:
                token = int(raw_token)
            except ValueError:
                token = 0

        return LeaseState(
            acquired=(
                owner == self.owner_id
                and (
                    token == 0
                    or self.fencing_token == 0
                    or token == self.fencing_token
                )
            ),
            owner_id=owner,
            expires_in_seconds=max(0, ttl),
            fencing_token=token,
        )
