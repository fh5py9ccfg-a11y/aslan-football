import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.cache import MemoryCache, CacheNamespace, NamespacedCache

class NamespacedCacheTests(unittest.TestCase):
    def test_namespace_versions_isolate_values(self):
        adapter = MemoryCache()
        v1 = NamespacedCache(adapter, CacheNamespace("fixture", 1))
        v2 = NamespacedCache(adapter, CacheNamespace("fixture", 2))
        v1.set("1", "old", 60)
        v2.set("1", "new", 60)
        self.assertEqual(v1.get("1"), "old")
        self.assertEqual(v2.get("1"), "new")

if __name__ == "__main__":
    unittest.main()
