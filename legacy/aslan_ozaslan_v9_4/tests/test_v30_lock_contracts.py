import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.locks import RedisDistributedLock, advisory_lock_key

class FakeRedis:
    def __init__(self):
        self.values = {}
    def set(self, key, value, *, nx, ex):
        if nx and key in self.values:
            return False
        self.values[key] = value
        return True
    def get(self, key):
        return self.values.get(key)
    def delete(self, key):
        return int(self.values.pop(key, None) is not None)

class LockContractTests(unittest.TestCase):
    def test_redis_owner_release(self):
        client = FakeRedis()
        lock = RedisDistributedLock(client)
        self.assertTrue(lock.acquire("scheduler", "node-a", 60))
        self.assertFalse(lock.acquire("scheduler", "node-b", 60))
        self.assertFalse(lock.release("scheduler", "node-b"))
        self.assertTrue(lock.release("scheduler", "node-a"))

    def test_postgres_key_is_deterministic(self):
        self.assertEqual(advisory_lock_key("sync"), advisory_lock_key("sync"))

if __name__ == "__main__":
    unittest.main()
