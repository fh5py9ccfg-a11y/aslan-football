from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import time
import zipfile


SENSITIVE_KEYS = {
    "AUTH_TOKEN_SECRET",
    "MVP_AUTH_SECRET",
    "SESSION_MAINTENANCE_APPROVAL_SIGNING_SECRET",
    "COMPLIANCE_ATTESTATION_SECRET",
    "PROVIDER_API_KEY",
    "SPORTMONKS_API_TOKEN",
}


def sanitize_env(text: str) -> str:
    output = []
    for line in text.splitlines():
        if "=" not in line:
            output.append(line)
            continue
        key, value = line.split("=", 1)
        if key.strip() in SENSITIVE_KEYS:
            output.append(f"{key}=***REDACTED***")
        else:
            output.append(f"{key}={value}")
    return "\n".join(output) + "\n"


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    generated = int(time.time())
    bundle_dir = root / ".support_bundle"
    if bundle_dir.exists():
        import shutil
        shutil.rmtree(bundle_dir)
    bundle_dir.mkdir(parents=True)

    subprocess.run(
        ["python", "scripts/diagnose.py"],
        cwd=root,
        capture_output=True,
        text=True,
    )

    for filename in (
        "DIAGNOSTIC_REPORT.json",
        "TEST_RESULTS.txt",
        "FINAL_RUNTIME_PATCH.json",
        "FINAL_PACKAGE_MANIFEST.json",
        "DELIVERY_MANIFEST.json",
        "SIGNED_RELEASE_MANIFEST.json",
    ):
        source = root / filename
        if source.exists():
            (bundle_dir / filename).write_bytes(
                source.read_bytes()
            )

    env_path = root / ".env"
    if env_path.exists():
        (bundle_dir / "env.redacted").write_text(
            sanitize_env(
                env_path.read_text(encoding="utf-8")
            ),
            encoding="utf-8",
        )

    metadata = {
        "generated_at": generated,
        "release": "v1.0.2",
        "note": "Secret values are redacted.",
    }
    (bundle_dir / "BUNDLE_INFO.json").write_text(
        json.dumps(
            metadata,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    output = root / f"aslan_support_bundle_{generated}.zip"
    with zipfile.ZipFile(
        output,
        "w",
        zipfile.ZIP_DEFLATED,
    ) as archive:
        for file in bundle_dir.rglob("*"):
            if file.is_file():
                archive.write(
                    file,
                    file.relative_to(bundle_dir),
                )

    import shutil
    shutil.rmtree(bundle_dir)
    print(output)


if __name__ == "__main__":
    main()
