import sys, tempfile, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operations import EncryptedBackupService

class EncryptedBackupTests(unittest.TestCase):
    def test_encrypt_decrypt_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.db"
            encrypted = Path(directory) / "backup.enc"
            restored = Path(directory) / "restored.db"
            source.write_bytes(b"critical-database-content")
            service = EncryptedBackupService()
            key = b"k" * 32
            result = service.encrypt(source, encrypted, key)
            self.assertGreater(result.bytes_written, source.stat().st_size)
            service.decrypt(encrypted, restored, key)
            self.assertEqual(restored.read_bytes(), source.read_bytes())

if __name__ == "__main__":
    unittest.main()
