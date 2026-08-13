from __future__ import annotations

from fastapi import WebSocket
from .security import token_service

async def authenticate_websocket(
    websocket: WebSocket,
    *,
    allowed_roles: tuple[str, ...],
):
    token = (
        websocket.query_params.get("access_token")
        or websocket.headers.get(
            "Authorization",
            "",
        ).removeprefix("Bearer ").strip()
    )

    if not token:
        await websocket.close(code=4401)
        return None

    try:
        principal = token_service.verify(token)
    except ValueError:
        await websocket.close(code=4401)
        return None

    if not set(allowed_roles).intersection(
        principal.roles
    ):
        await websocket.close(code=4403)
        return None

    return principal
