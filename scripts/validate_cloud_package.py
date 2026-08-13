from __future__ import annotations

from pathlib import Path
import json
import re
import sys


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    required = (
        "Dockerfile",
        "render.yaml",
        "railway.json",
        "scripts/cloud_start.sh",
        "QUICK_ENSEMBLE_MODEL.json",
        "apps/api/app/static/manifest.webmanifest",
        "apps/api/app/static/sw.js",
    )
    missing = [
        name for name in required
        if not (root / name).exists()
    ]

    dockerfile = (root / "Dockerfile").read_text(encoding="utf-8")
    start_script = (
        root / "scripts/cloud_start.sh"
    ).read_text(encoding="utf-8")
    render_yaml = (
        root / "render.yaml"
    ).read_text(encoding="utf-8")

    checks = {
        "missing_files": missing,
        "docker_copies_model": (
            "QUICK_ENSEMBLE_MODEL.json" in dockerfile
        ),
        "dynamic_port": "${PORT:-10000}" in start_script,
        "database_url_normalization": (
            "postgresql+psycopg://" in start_script
        ),
        "health_check": "healthCheckPath: /health" in render_yaml,
        "postgres_defined": "databases:" in render_yaml,
        "redis_defined": "type: keyvalue" in render_yaml,
    }
    ok = not missing and all(
        value for key, value in checks.items()
        if key != "missing_files"
    )
    payload = {"ok": ok, "checks": checks}
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
