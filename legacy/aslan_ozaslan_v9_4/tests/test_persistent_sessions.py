import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.security import SQLiteSessionStore

class PersistentSessionTests(unittest.TestCase):
    def test_create_get_revoke(self):
        with tempfile.TemporaryDirectory() as directory:
            store = SQLiteSessionStore(Path(directory) / "sessions.db")
            token = store.create("u1", "OWNER", ttl_minutes=5)
            self.assertIsNotNone(store.get(token))
            store.revoke(token)
            self.assertIsNone(store.get(token))

if __name__ == "__main__":
    unittest.main()
