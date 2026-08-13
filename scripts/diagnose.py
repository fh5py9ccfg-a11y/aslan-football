from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen


def run(command: list[str], cwd: Path) -> dict:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return {
            "command": " ".join(command),
            "returncode": completed.returncode,
            "stdout": completed.stdout[-6000:],
            "stderr": completed.stderr[-6000:],
        }
    except Exception as exc:
        return {
            "command": " ".join(command),
            "returncode": -1,
            "stdout": "",
            "stderr": str(exc),
        }


def read_health(base_url: str) -> dict:
    try:
        with urlopen(
            f"{base_url.rstrip('/')}/health",
            timeout=10,
        ) as response:
            payload = json.loads(
                response.read().decode("utf-8")
            )
            return {
                "ok": response.status == 200,
                "status": response.status,
                "payload": payload,
            }
    except Exception as exc:
        return {
            "ok": False,
            "error": str(exc),
        }


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    )
    docker_available = shutil.which("docker") is not None

    report = {
        "generated_at": int(time.time()),
        "release": "v1.0.2",
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "python": sys.version,
        },
        "files": {
            "env_exists": (root / ".env").exists(),
            "compose_exists": (root / "docker-compose.yml").exists(),
            "test_results_exists": (root / "TEST_RESULTS.txt").exists(),
        },
        "docker_available": docker_available,
        "health": read_health(base_url),
        "commands": [],
    }

    if docker_available:
        report["commands"].append(
            run(
                ["docker", "compose", "ps", "--all"],
                root,
            )
        )
        report["commands"].append(
            run(
                [
                    "docker",
                    "compose",
                    "logs",
                    "--tail",
                    "120",
                    "api",
                ],
                root,
            )
        )
        report["commands"].append(
            run(
                [
                    "docker",
                    "compose",
                    "logs",
                    "--tail",
                    "80",
                    "redis",
                ],
                root,
            )
        )

    target = root / "DIAGNOSTIC_REPORT.json"
    target.write_text(
        json.dumps(
            report,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))

    critical_ok = (
        report["files"]["compose_exists"]
        and report["health"]["ok"]
    )
    return 0 if critical_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
