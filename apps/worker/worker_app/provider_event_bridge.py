from __future__ import annotations
import httpx

EVENT_MAP = {
    "goal": "GOAL",
    "redcard": "RED_CARD",
}

class ProviderEventToApiBridge:
    def __init__(
        self,
        *,
        api_base_url: str,
        client: httpx.AsyncClient | None = None,
        provider_api_key_id: str | None = None,
        provider_api_key: str | None = None,
    ):
        self.api_base_url = api_base_url.rstrip("/")
        self.client = client or httpx.AsyncClient(timeout=10.0)
        self._owns_client = client is None
        self.provider_api_key_id = provider_api_key_id
        self.provider_api_key = provider_api_key

    async def close(self):
        if self._owns_client:
            await self.client.aclose()

    async def handle(self, message) -> None:
        payload = message.payload
        raw_type = str(
            payload.get("type", {}).get("developer_name")
            or payload.get("type_name")
            or ""
        ).lower()
        event_type = EVENT_MAP.get(raw_type)
        if event_type is None:
            return

        team = payload.get("team")
        if team is None:
            location = str(
                payload.get("participant", {}).get("meta", {}).get("location", "")
            ).upper()
            team = location if location in {"HOME", "AWAY"} else None

        fixture_id = str(payload["fixture_id"])
        sequence = int(payload.get("sort_order") or payload["id"])
        body = {
            "fixture_id": fixture_id,
            "sequence": sequence,
            "event_type": event_type,
            "minute": int(payload["minute"]),
            "team": team,
        }
        response = await self.client.post(
            f"{self.api_base_url}/fixtures/{fixture_id}/events",
            json=body,
            headers={
                "X-Correlation-ID": message.message_id,
                **(
                    {
                        "X-API-Key-ID": self.provider_api_key_id,
                        "X-API-Key": self.provider_api_key,
                    }
                    if self.provider_api_key_id and self.provider_api_key
                    else {}
                ),
            },
        )
        if response.status_code not in {200, 409}:
            response.raise_for_status()
