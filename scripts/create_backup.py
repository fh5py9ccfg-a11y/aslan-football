from __future__ import annotations

import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


def main() -> None:
    base_url = os.getenv(
        "ASLAN_BASE_URL",
        "http://localhost:8000",
    ).rstrip("/")
    club_id = os.getenv(
        "ASLAN_CLUB_ID",
        "demo-aslan",
    )
    backup_id = os.getenv(
        "ASLAN_BACKUP_ID",
        "manual-backup",
    )
    query = urlencode({
        "backup_id": backup_id,
    })
    request = Request(
        f"{base_url}/mvp/stabilization/"
        f"{club_id}/backup?{query}",
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        payload = json.loads(
            response.read().decode("utf-8")
        )

    target = Path(
        os.getenv(
            "ASLAN_BACKUP_FILE",
            f"{backup_id}.json",
        )
    )
    target.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(target)


if __name__ == "__main__":
    main()
