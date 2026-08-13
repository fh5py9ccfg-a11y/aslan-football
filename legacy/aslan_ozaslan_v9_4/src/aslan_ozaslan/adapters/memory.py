from datetime import datetime, timezone
from aslan_ozaslan.adapters.base import ProviderHealth
from aslan_ozaslan.models import MatchInput

class InMemoryDataProvider:
    name = "in-memory"

    def __init__(self, matches: dict[str, MatchInput]):
        self._matches = dict(matches)

    def fetch_match(self, fixture_id: str) -> MatchInput:
        try:
            return self._matches[fixture_id]
        except KeyError as exc:
            raise LookupError(f"Maç bulunamadı: {fixture_id}") from exc

    def health(self) -> ProviderHealth:
        return ProviderHealth(
            provider_name=self.name,
            healthy=True,
            checked_at=datetime.now(timezone.utc),
            message="Bellek içi test sağlayıcısı çalışıyor.",
        )
