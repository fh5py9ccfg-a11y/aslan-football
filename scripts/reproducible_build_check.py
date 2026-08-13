from __future__ import annotations

import hashlib
import json
from pathlib import Path


def file_manifest(root: Path) -> dict:
    files = []
    for path in sorted(root.rglob("*")):
        if (
            not path.is_file()
            or "__pycache__" in path.parts
            or ".pytest_cache" in path.parts
            or path.name in {
                "DELIVERY_MANIFEST.json",
                "SBOM.json",
                "REPRODUCIBLE_BUILD_REPORT.json",
            }
        ):
            continue
        files.append({
            "path": str(path.relative_to(root)),
            "sha256": hashlib.sha256(
                path.read_bytes()
            ).hexdigest(),
        })
    return {
        "build_version": "build-024-supply-chain",
        "files": files,
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    first = file_manifest(root)
    second = file_manifest(root)
    first_checksum = hashlib.sha256(
        json.dumps(
            first,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    second_checksum = hashlib.sha256(
        json.dumps(
            second,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    ).hexdigest()
    payload = {
        "first_manifest_checksum": first_checksum,
        "second_manifest_checksum": second_checksum,
        "deterministic": first_checksum == second_checksum,
    }
    target = root / "REPRODUCIBLE_BUILD_REPORT.json"
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["deterministic"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
