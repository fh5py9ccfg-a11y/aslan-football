from __future__ import annotations

import json
import os
from urllib.request import urlopen


def main() -> int:
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    club_id = os.getenv(
        "ASLAN_CLUB_ID",
        "final-pilot-club",
    )
    with urlopen(
        f"{base_url}/mvp/pilot-acceptance/"
        f"{club_id}/repeatability",
        timeout=60,
    ) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("stable") else 1


if __name__ == "__main__":
    raise SystemExit(main())
