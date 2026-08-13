import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.ingestion import RawPayload, SQLiteRawArchive


class RawArchiveTests(unittest.TestCase):
    def test_same_payload_is_not_duplicated(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = SQLiteRawArchive(Path(directory) / "raw.db")
            record = RawPayload.create(
                provider="provider-a",
                resource_type="fixture",
                external_id="fx-1",
                payload={"status": "scheduled", "home": "A", "away": "B"},
            )
            self.assertTrue(archive.append(record))
            self.assertFalse(archive.append(record))
            self.assertEqual(len(archive.history("provider-a", "fixture", "fx-1")), 1)

    def test_changed_payload_creates_new_version(self):
        with tempfile.TemporaryDirectory() as directory:
            archive = SQLiteRawArchive(Path(directory) / "raw.db")
            first = RawPayload.create(
                provider="provider-a",
                resource_type="fixture",
                external_id="fx-2",
                payload={"status": "scheduled"},
            )
            second = RawPayload.create(
                provider="provider-a",
                resource_type="fixture",
                external_id="fx-2",
                payload={"status": "postponed"},
            )
            archive.append(first)
            archive.append(second)
            self.assertEqual(len(archive.history("provider-a", "fixture", "fx-2")), 2)


if __name__ == "__main__":
    unittest.main()
