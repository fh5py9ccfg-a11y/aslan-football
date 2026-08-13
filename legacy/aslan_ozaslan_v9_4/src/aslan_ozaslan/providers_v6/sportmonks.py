from __future__ import annotations
from dataclasses import dataclass

from .config import SportmonksConfig
from .http import HttpTransport

class ProviderNotConnected(RuntimeError):
    pass

@dataclass(frozen=True)
class ProviderPage:
    data: tuple[dict, ...]
    current_page: int
    has_more: bool

class SportmonksClient:
    def __init__(
        self,
        *,
        config: SportmonksConfig,
        transport: HttpTransport,
    ):
        config.validate()
        self.config = config
        self.transport = transport

    def _headers(self) -> dict[str, str]:
        if not self.config.api_token:
            raise ProviderNotConnected(
                "SPORTMONKS_API_TOKEN tanımlı değil; dış istek gönderilmedi."
            )
        return {
            "Authorization": self.config.api_token,
            "Accept": "application/json",
            "User-Agent": "Aslan-Ozaslan/6.3",
        }

    def _get(self, path: str, params: dict | None = None) -> dict:
        response = self.transport.get(
            url=self.config.base_url + path,
            headers=self._headers(),
            params=params or {},
            timeout_seconds=self.config.timeout_seconds,
        )
        if response.status_code != 200:
            raise RuntimeError(
                f"Sportmonks HTTP hatası: {response.status_code}"
            )
        return response.payload

    def fixture_by_id(
        self,
        fixture_id: int,
        *,
        include: str = "participants;state;scores",
    ) -> dict:
        if fixture_id <= 0:
            raise ValueError("fixture_id pozitif olmalıdır")
        payload = self._get(
            f"/fixtures/{fixture_id}",
            {"include": include},
        )
        return dict(payload.get("data") or {})

    def inplay_livescores(
        self,
        *,
        include: str = "participants;state;scores;events;statistics",
    ) -> tuple[dict, ...]:
        payload = self._get(
            "/livescores/inplay",
            {"include": include},
        )
        return tuple(payload.get("data") or ())

    def latest_updated_livescores(
        self,
        *,
        include: str = "participants;state;scores;events",
    ) -> tuple[dict, ...]:
        payload = self._get(
            "/livescores/latest",
            {"include": include},
        )
        return tuple(payload.get("data") or ())

    def fixtures_by_date(
        self,
        date: str,
        *,
        include: str = "participants;state;scores",
    ) -> tuple[dict, ...]:
        all_items = []
        page = 1

        while page <= self.config.max_pages:
            payload = self._get(
                f"/fixtures/date/{date}",
                {
                    "include": include,
                    "per_page": self.config.per_page,
                    "page": page,
                },
            )
            all_items.extend(payload.get("data") or ())
            pagination = payload.get("pagination") or {}
            if not pagination.get("has_more", False):
                return tuple(all_items)
            page += 1

        raise RuntimeError(
            "Sportmonks sayfalama güvenlik sınırı aşıldı; "
            "eksik veri tamamlanmış sayılmadı."
        )
