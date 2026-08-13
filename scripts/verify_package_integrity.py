from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("package")
    parser.add_argument("expected_checksum")
    parser.add_argument(
        "--manifest",
        default="DELIVERY_MANIFEST.json",
    )
    args = parser.parse_args()

    package_path = Path(args.package)
    manifest_path = Path(args.manifest)
    actual = hashlib.sha256(
        package_path.read_bytes()
    ).hexdigest()
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    result = {
        "package": str(package_path),
        "expected_checksum": args.expected_checksum,
        "actual_checksum": actual,
        "checksum_valid": actual == args.expected_checksum,
        "manifest_build": manifest.get("build_version"),
        "manifest_tests": manifest.get("tests_passed"),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["checksum_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
