from __future__ import annotations
from dataclasses import dataclass
import os

@dataclass(frozen=True)
class SportmonksConfig:
    api_token: str | None
    base_url: str = "https://api.sportmonks.com/v3/football"
    timeout_seconds: float = 8.0
    max_pages: int = 20
    per_page: int = 50

    @classmethod
    def from_environment(cls) -> "SportmonksConfig":
        token = os.getenv("SPORTMONKS_API_TOKEN")
        return cls(
            api_token=token.strip() if token and token.strip() else None,
            base_url=os.getenv(
                "SPORTMONKS_BASE_URL",
                "https://api.sportmonks.com/v3/football",
            ).rstrip("/"),
            timeout_seconds=float(
                os.getenv("SPORTMONKS_TIMEOUT_SECONDS", "8")
            ),
            max_pages=int(os.getenv("SPORTMONKS_MAX_PAGES", "20")),
            per_page=int(os.getenv("SPORTMONKS_PER_PAGE", "50")),
        )

    @property
    def connected(self) -> bool:
        return bool(self.api_token)

    def validate(self) -> None:
        if self.timeout_seconds <= 0:
            raise ValueError("timeout_seconds pozitif olmalıdır")
        if not 1 <= self.max_pages <= 100:
            raise ValueError("max_pages 1-100 arasında olmalıdır")
        if not 1 <= self.per_page <= 50:
            raise ValueError("per_page 1-50 arasında olmalıdır")
