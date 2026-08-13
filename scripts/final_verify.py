from __future__ import annotations

import json
import os
import subprocess
import sys


def run(command: list[str]) -> dict:
    completed = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def main() -> int:
    checks = [
        run([sys.executable, "scripts/smoke_test.py"]),
        run([sys.executable, "scripts/load_probe.py"]),
        run([sys.executable, "scripts/final_pilot_setup.py"]),
    ]
    ok = all(item["returncode"] == 0 for item in checks)
    print(json.dumps({"ok": ok, "checks": checks}, ensure_ascii=False, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
