from __future__ import annotations

import hashlib
import importlib.metadata
import json
from pathlib import Path


LICENSE_MAP = {
    "fastapi": "MIT",
    "redis": "MIT",
    "pydantic": "MIT",
    "uvicorn": "BSD-3-Clause",
    "pytest": "MIT",
    "httpx": "BSD-3-Clause",
}


def main() -> None:
    dependencies = []
    for distribution in importlib.metadata.distributions():
        name = (
            distribution.metadata.get("Name")
            or "unknown"
        )
        version = distribution.version
        normalized = name.lower()
        license_name = LICENSE_MAP.get(
            normalized,
            (
                distribution.metadata.get("License")
                or "UNKNOWN"
            ),
        )
        checksum = hashlib.sha256(
            f"{name}=={version}".encode("utf-8")
        ).hexdigest()
        dependencies.append({
            "name": name,
            "version": version,
            "source": "python-environment",
            "license": str(license_name).upper(),
            "checksum": checksum,
        })

    dependencies.sort(
        key=lambda item: item["name"].lower()
    )
    payload = {
        "format": "aslan-sbom-1",
        "build_version": "build-024-supply-chain",
        "dependencies": dependencies,
    }
    target = (
        Path(__file__).resolve().parents[1]
        / "SBOM.json"
    )
    target.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()
