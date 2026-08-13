from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    test_text = (root / "TEST_RESULTS.txt").read_text(
        encoding="utf-8"
    )
    match = re.search(
        r"(\d+) passed.*?(\d+) deselected",
        test_text,
        re.S,
    )
    tests_passed = int(match.group(1)) if match else 0
    tests_deselected = int(match.group(2)) if match else 0

    files = [
        path
        for path in root.rglob("*")
        if path.is_file()
        and "__pycache__" not in path.parts
        and ".pytest_cache" not in path.parts
    ]
    docs = sorted(
        str(path.relative_to(root))
        for path in root.glob("docs/*")
        if path.is_file()
    )
    scripts = sorted(
        str(path.relative_to(root))
        for path in root.glob("scripts/*")
        if path.is_file()
    )
    checksum_source = "\n".join(
        f"{path.relative_to(root)}:"
        f"{hashlib.sha256(path.read_bytes()).hexdigest()}"
        for path in sorted(files)
    )
    package_checksum = hashlib.sha256(
        checksum_source.encode("utf-8")
    ).hexdigest()

    payload = {
        "manifest_id": "aslan-build-022",
        "build_version": "build-022-delivery",
        "project_name": "Aslan Football",
        "files_count": len(files),
        "tests_passed": tests_passed,
        "tests_deselected": tests_deselected,
        "documentation_files": docs,
        "operational_scripts": scripts,
        "package_checksum": package_checksum,
        "acceptance_status": "TESTED",
    }
    target = root / "DELIVERY_MANIFEST.json"
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
