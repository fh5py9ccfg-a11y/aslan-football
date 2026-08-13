from __future__ import annotations
import asyncio
import logging

logger = logging.getLogger(__name__)

class OidcMetadataRefresher:
    def __init__(
        self,
        *,
        discovery_cache=None,
        jwks_cache=None,
        interval_seconds: float = 60.0,
    ):
        if interval_seconds <= 0:
            raise ValueError("interval_seconds pozitif olmalıdır")
        self.discovery_cache = discovery_cache
        self.jwks_cache = jwks_cache
        self.interval_seconds = interval_seconds
        self._task: asyncio.Task | None = None
        self._stopping = asyncio.Event()

    async def start(self) -> None:
        if self._task is None:
            self._task = asyncio.create_task(
                self._run(),
                name="oidc-metadata-refresher",
            )

    async def stop(self) -> None:
        self._stopping.set()
        if self._task is not None:
            await self._task
            self._task = None

    async def run_once(self) -> dict:
        result = {
            "discovery": "skipped",
            "jwks": "skipped",
        }

        if self.discovery_cache is not None:
            try:
                self.discovery_cache.get(
                    force_refresh=True
                )
                result["discovery"] = "ok"
            except Exception as exc:
                logger.warning(
                    "OIDC discovery refresh failed: %s",
                    exc,
                )
                result["discovery"] = "error"

        if self.jwks_cache is not None:
            try:
                self.jwks_cache.refresh()
                result["jwks"] = "ok"
            except Exception as exc:
                logger.warning(
                    "JWKS refresh failed: %s",
                    exc,
                )
                result["jwks"] = "error"

        return result

    async def _run(self) -> None:
        while not self._stopping.is_set():
            await self.run_once()
            try:
                await asyncio.wait_for(
                    self._stopping.wait(),
                    timeout=self.interval_seconds,
                )
            except asyncio.TimeoutError:
                pass
