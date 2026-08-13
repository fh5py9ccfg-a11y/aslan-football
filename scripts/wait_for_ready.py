from __future__ import annotations

import json
import os
import time
from urllib.request import urlopen


def main() -> int:
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    timeout_seconds = int(
        os.getenv("ASLAN_STARTUP_TIMEOUT_SECONDS", "120")
    )
    deadline = time.monotonic() + timeout_seconds
    last_error = ""

    while time.monotonic() < deadline:
        try:
            with urlopen(
                f"{base_url}/health",
                timeout=5,
            ) as response:
                payload = json.loads(
                    response.read().decode("utf-8")
                )
                if response.status == 200:
                    print(
                        json.dumps(
                            {
                                "ready": True,
                                "health": payload,
                            },
                            ensure_ascii=False,
                            indent=2,
                        )
                    )
                    return 0
        except Exception as exc:
            last_error = str(exc)

        time.sleep(2)

    print(
        json.dumps(
            {
                "ready": False,
                "timeout_seconds": timeout_seconds,
                "last_error": last_error,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
