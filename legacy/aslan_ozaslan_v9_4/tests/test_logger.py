import sys, tempfile, unittest, json
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.observability import JsonEventLogger

class LoggerTests(unittest.TestCase):
    def test_secrets_are_redacted(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "events.jsonl"
            logger = JsonEventLogger(path)
            logger.write("login", {"email":"a@b.com","password":"secret","token":"abc"})
            record = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(record["payload"]["password"], "[REDACTED]")
            self.assertEqual(record["payload"]["token"], "[REDACTED]")

if __name__ == "__main__":
    unittest.main()
