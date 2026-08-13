from __future__ import annotations
from dataclasses import dataclass

from .config import SportmonksConfig

@dataclass(frozen=True)
class ProviderConnectionStatus:
    provider: str
    connected: bool
    label: str
    request_allowed: bool

class ProviderConnectionInspector:
    def inspect_sportmonks(
        self,
        config: SportmonksConfig,
    ) -> ProviderConnectionStatus:
        if not config.connected:
            return ProviderConnectionStatus(
                provider="sportmonks",
                connected=False,
                label="bağlantı bekliyor",
                request_allowed=False,
            )
        return ProviderConnectionStatus(
            provider="sportmonks",
            connected=True,
            label="anahtar tanımlı",
            request_allowed=True,
        )
