from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import hashlib
import shutil


@dataclass(frozen=True)
class BackupResult:
    source: str
    destination: str
    sha256: str
    bytes_copied: int


class FileBackupService:
    def backup(self, source: str | Path, destination: str | Path) -> BackupResult:
        source_path = Path(source)
        destination_path = Path(destination)
        if not source_path.is_file():
            raise FileNotFoundError(source_path)
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_path, destination_path)

        digest = hashlib.sha256(destination_path.read_bytes()).hexdigest()
        return BackupResult(
            source=str(source_path),
            destination=str(destination_path),
            sha256=digest,
            bytes_copied=destination_path.stat().st_size,
        )

    def verify(self, backup: BackupResult) -> bool:
        destination = Path(backup.destination)
        if not destination.is_file():
            return False
        return (
            destination.stat().st_size == backup.bytes_copied
            and hashlib.sha256(destination.read_bytes()).hexdigest() == backup.sha256
        )
