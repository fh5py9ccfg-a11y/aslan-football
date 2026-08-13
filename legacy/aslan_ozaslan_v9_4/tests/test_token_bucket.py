import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.rate_limit import TokenBucket

class TokenBucketTests(unittest.TestCase):
    def test_blocks_when_tokens_exhausted(self):
        bucket = TokenBucket(capacity=2, refill_rate_per_second=0.0001)
        self.assertTrue(bucket.allow())
        self.assertTrue(bucket.allow())
        self.assertFalse(bucket.allow())

if __name__ == "__main__":
    unittest.main()
