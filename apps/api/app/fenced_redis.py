from .distributed_lease import StaleFencingToken

class FencedRedisMutator:
    REMOVE_SCRIPT = '''
    local current = tonumber(redis.call("GET", KEYS[1]) or "0")
    local expected = tonumber(ARGV[1])
    if expected < current then
        return {-1, current}
    end
    redis.call("SET", KEYS[1], expected)
    return {redis.call("SREM", KEYS[2], ARGV[2]), expected}
    '''

    EXPIRE_SCRIPT = '''
    local current = tonumber(redis.call("GET", KEYS[1]) or "0")
    local expected = tonumber(ARGV[1])
    if expected < current then
        return {-1, current}
    end
    redis.call("SET", KEYS[1], expected)
    return {redis.call("EXPIRE", KEYS[2], ARGV[2]), expected}
    '''

    DELETE_SCRIPT = '''
    local current = tonumber(redis.call("GET", KEYS[1]) or "0")
    local expected = tonumber(ARGV[1])
    if expected < current then
        return {-1, current}
    end
    redis.call("SET", KEYS[1], expected)
    return {redis.call("DEL", KEYS[2]), expected}
    '''

    def __init__(self, client, *, fencing_token, fence_key):
        if fencing_token <= 0:
            raise ValueError("fencing_token pozitif olmalıdır")
        self.client = client
        self.fencing_token = fencing_token
        self.fence_key = fence_key

    def remove_orphan(self, index_key, session_id):
        return self._result(self.client.eval(
            self.REMOVE_SCRIPT,
            2,
            self.fence_key,
            index_key,
            self.fencing_token,
            session_id,
        ))

    def expire_index(self, index_key, ttl):
        return self._result(self.client.eval(
            self.EXPIRE_SCRIPT,
            2,
            self.fence_key,
            index_key,
            self.fencing_token,
            ttl,
        ))

    def delete_index(self, index_key):
        return self._result(self.client.eval(
            self.DELETE_SCRIPT,
            2,
            self.fence_key,
            index_key,
            self.fencing_token,
        ))

    @staticmethod
    def _result(result):
        code = int(result[0])
        if code == -1:
            raise StaleFencingToken(
                "Bakım fencing token eski; yazma reddedildi"
            )
        return code
