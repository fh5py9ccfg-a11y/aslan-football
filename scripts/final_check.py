from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def run(command: list[str], cwd: Path) -> dict:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return {
        "command": " ".join(command),
        "returncode": completed.returncode,
        "stdout": completed.stdout[-4000:],
        "stderr": completed.stderr[-4000:],
    }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checks = []

    checks.append(
        run(
            [
                sys.executable,
                "-m",
                "pytest",
                "-q",
                "-m",
                "not integration",
            ],
            root,
        )
    )

    for script in (
        "scripts/wait_for_ready.py",
        "scripts/diagnose.py",
        "scripts/smoke_test.py",
        "scripts/load_probe.py",
        "scripts/final_pilot_setup.py",
        "scripts/pilot_acceptance.py",
        "scripts/repeatability_check.py",
    ):
        if os.getenv("ASLAN_SKIP_RUNTIME_CHECKS") == "1":
            break
        checks.append(
            run([sys.executable, script], root)
        )

    ok = all(item["returncode"] == 0 for item in checks)
    report = {
        "project": "Aslan Football Final",
        "ok": ok,
        "checks": checks,
    }
    target = root / "FINAL_CHECK_REPORT.json"
    target.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
