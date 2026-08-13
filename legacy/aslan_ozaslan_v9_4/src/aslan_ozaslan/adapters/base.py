from dataclasses import dataclass
from datetime import datetime
from typing import Protocol
from aslan_ozaslan.models import MatchInput

@dataclass(frozen=True)
class ProviderHealth:
    provider_name: str
    healthy: bool
    checked_at: datetime
    message: str

class DataProvider(Protocol):
    name: str
    def fetch_match(self, fixture_id: str) -> MatchInput: ...
    def health(self) -> ProviderHealth: ...
