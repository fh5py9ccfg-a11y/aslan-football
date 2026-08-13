from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    manifest_path = root / "DELIVERY_MANIFEST.json"
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )
    manifest_checksum = hashlib.sha256(
        manifest_path.read_bytes()
    ).hexdigest()
    acceptance_fingerprint = os.getenv(
        "ASLAN_ACCEPTANCE_FINGERPRINT",
        "not-provided",
    )
    signing_key = os.getenv(
        "ASLAN_RELEASE_SIGNING_KEY",
    )
    if not signing_key or len(signing_key) < 24:
        raise SystemExit(
            "ASLAN_RELEASE_SIGNING_KEY en az 24 karakter olmalıdır"
        )
    canonical = json.dumps(
        {
            "build_version": "build-023-release-freeze",
            "package_checksum": manifest["package_checksum"],
            "source_manifest_checksum": manifest_checksum,
            "acceptance_fingerprint": acceptance_fingerprint,
        },
        sort_keys=True,
        separators=(",", ":"),
    )
    signature = hashlib.sha256(
        (signing_key + canonical).encode("utf-8")
    ).hexdigest()
    payload = {
        "build_version": "build-023-release-freeze",
        "package_checksum": manifest["package_checksum"],
        "source_manifest_checksum": manifest_checksum,
        "acceptance_fingerprint": acceptance_fingerprint,
        "signature": signature,
        "immutable": True,
    }
    target = root / "SIGNED_RELEASE_MANIFEST.json"
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()
