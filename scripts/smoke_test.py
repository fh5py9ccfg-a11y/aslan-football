from __future__ import annotations

import json
import os
import sys
from urllib.request import urlopen


def main() -> int:
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    endpoints = (
        "/health",
        "/mvp/stabilization/smoke",
        "/mvp/mobile/config",
    )
    failures = []
    results = {}

    for endpoint in endpoints:
        try:
            with urlopen(
                f"{base_url}{endpoint}",
                timeout=10,
            ) as response:
                payload = json.loads(
                    response.read().decode("utf-8")
                )
                results[endpoint] = {
                    "status": response.status,
                    "payload": payload,
                }
        except Exception as exc:
            failures.append(
                f"{endpoint}: {exc}"
            )

    print(
        json.dumps(
            {
                "ok": not failures,
                "results": results,
                "failures": failures,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
