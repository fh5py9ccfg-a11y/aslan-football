from __future__ import annotations

import json
import os
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def main() -> int:
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    club_id = os.getenv(
        "ASLAN_CLUB_ID",
        "final-pilot-club",
    )
    query = urlencode({
        "report_id": "cli-pilot-acceptance",
        "reviewer": "cli",
    })
    request = Request(
        f"{base_url}/mvp/pilot-acceptance/"
        f"{club_id}/run?{query}",
        method="POST",
    )
    with urlopen(request, timeout=90) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )

    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if payload.get("status") == "ACCEPTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
