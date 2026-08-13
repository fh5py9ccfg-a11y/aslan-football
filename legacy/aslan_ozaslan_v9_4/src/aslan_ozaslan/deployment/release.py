from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
from pathlib import Path


@dataclass(frozen=True)
class ReleaseArtifact:
    version: str
    path: str
    sha256: str
    created_at: str


class ReleaseManager:
    def build_manifest(self, version: str, artifact_path: str | Path) -> ReleaseArtifact:
        if not version.strip():
            raise ValueError("Sürüm boş olamaz")
        path = Path(artifact_path)
        if not path.is_file():
            raise FileNotFoundError(path)

        return ReleaseArtifact(
            version=version,
            path=str(path),
            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
            created_at=datetime.now(timezone.utc).isoformat(),
        )

    def verify(self, artifact: ReleaseArtifact) -> bool:
        path = Path(artifact.path)
        if not path.is_file():
            return False
        return hashlib.sha256(path.read_bytes()).hexdigest() == artifact.sha256
