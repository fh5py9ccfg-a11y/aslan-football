from __future__ import annotations
import os

from fastapi import Header, HTTPException

from .api_key_registry import InMemoryApiKeyRegistry

_registry = None

def configure_api_key_registry(registry):
    global _registry
    _registry = registry

def build_default_registry():
    registry = InMemoryApiKeyRegistry()
    for item in os.getenv("PROVIDER_API_KEYS", "").split(","):
        item = item.strip()
        if not item:
            continue
        key_id, secret = item.split(":", 1)
        registry.upsert(
            key_id=key_id,
            secret=secret,
            roles=("provider",),
        )
    return registry

def current_registry():
    global _registry
    if _registry is None:
        _registry = build_default_registry()
    return _registry

def provider_api_key(
    x_api_key_id: str | None = Header(
        default=None,
        alias="X-API-Key-ID",
    ),
    x_api_key: str | None = Header(
        default=None,
        alias="X-API-Key",
    ),
):
    if not x_api_key_id or not x_api_key:
        raise HTTPException(
            status_code=401,
            detail="X-API-Key-ID ve X-API-Key gerekli",
        )
    try:
        return current_registry().verify(
            key_id=x_api_key_id,
            raw_secret=x_api_key,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc
