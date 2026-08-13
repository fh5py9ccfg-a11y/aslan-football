from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import hmac
import os


@dataclass(frozen=True)
class EncryptedBackupResult:
    destination: str
    bytes_written: int
    sha256: str


class EncryptedBackupService:
    HEADER = b"ASLANBK1"

    def encrypt(self, source: str | Path, destination: str | Path, key: bytes) -> EncryptedBackupResult:
        if len(key) < 32:
            raise ValueError("Yedekleme anahtarı en az 32 bayt olmalıdır")

        source_path = Path(source)
        destination_path = Path(destination)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)

        plaintext = source_path.read_bytes()
        nonce = os.urandom(16)
        ciphertext = self._xor_stream(plaintext, key, nonce)
        tag = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        payload = self.HEADER + nonce + tag + ciphertext

        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(payload)

        return EncryptedBackupResult(
            destination=str(destination_path),
            bytes_written=len(payload),
            sha256=hashlib.sha256(payload).hexdigest(),
        )

    def decrypt(self, source: str | Path, destination: str | Path, key: bytes) -> None:
        source_path = Path(source)
        payload = source_path.read_bytes()
        if not payload.startswith(self.HEADER):
            raise ValueError("Geçersiz yedek başlığı")

        offset = len(self.HEADER)
        nonce = payload[offset:offset + 16]
        tag = payload[offset + 16:offset + 48]
        ciphertext = payload[offset + 48:]

        expected = hmac.new(key, nonce + ciphertext, hashlib.sha256).digest()
        if not hmac.compare_digest(tag, expected):
            raise ValueError("Yedek bütünlük doğrulaması başarısız")

        plaintext = self._xor_stream(ciphertext, key, nonce)
        destination_path = Path(destination)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(plaintext)

    def _xor_stream(self, data: bytes, key: bytes, nonce: bytes) -> bytes:
        output = bytearray()
        counter = 0
        while len(output) < len(data):
            block = hashlib.sha256(
                key + nonce + counter.to_bytes(8, "big")
            ).digest()
            output.extend(block)
            counter += 1
        return bytes(left ^ right for left, right in zip(data, output))
