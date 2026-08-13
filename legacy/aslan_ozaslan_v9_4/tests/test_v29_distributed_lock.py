import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.locks import InMemoryDistributedLock

class DistributedLockTests(unittest.TestCase):
    def test_single_owner(self):
        lock = InMemoryDistributedLock()
        self.assertTrue(lock.acquire("scheduler", "node-a", 60))
        self.assertFalse(lock.acquire("scheduler", "node-b", 60))
        self.assertFalse(lock.release("scheduler", "node-b"))
        self.assertTrue(lock.release("scheduler", "node-a"))

if __name__ == "__main__":
    unittest.main()
