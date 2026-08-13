from __future__ import annotations
import json
import secrets
import time
from dataclasses import dataclass

@dataclass(frozen=True)
class RedisWebSocketTicket:
    ticket: str
    subject: str
    roles: tuple[str, ...]
    expires_at: int

class RedisWebSocketTicketRepository:
    CONSUME_SCRIPT = '''
    local value = redis.call("GET", KEYS[1])
    if not value then
        return false
    end
    redis.call("DEL", KEYS[1])
    return value
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:ws-ticket",
    ):
        self.client = client
        self.prefix = prefix

    def issue(
        self,
        *,
        subject: str,
        roles: tuple[str, ...],
        ttl_seconds: int = 30,
    ) -> RedisWebSocketTicket:
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds pozitif olmalıdır")

        ticket = secrets.token_urlsafe(24)
        expires_at = int(time.time()) + ttl_seconds
        payload = json.dumps(
            {
                "subject": subject,
                "roles": list(roles),
                "expires_at": expires_at,
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )
        self.client.setex(
            f"{self.prefix}:{ticket}",
            ttl_seconds,
            payload,
        )
        return RedisWebSocketTicket(
            ticket=ticket,
            subject=subject,
            roles=tuple(roles),
            expires_at=expires_at,
        )

    def consume(
        self,
        ticket: str,
    ) -> RedisWebSocketTicket | None:
        payload = self.client.eval(
            self.CONSUME_SCRIPT,
            1,
            f"{self.prefix}:{ticket}",
        )
        if not payload:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")

        data = json.loads(payload)
        expires_at = int(data["expires_at"])
        if expires_at <= int(time.time()):
            return None

        return RedisWebSocketTicket(
            ticket=ticket,
            subject=str(data["subject"]),
            roles=tuple(
                str(item)
                for item in data.get("roles") or ()
            ),
            expires_at=expires_at,
        )

class RedisRevocationRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:revoked",
    ):
        self.client = client
        self.prefix = prefix

    def revoke(
        self,
        token_id: str,
        expires_at: int,
    ) -> None:
        ttl = max(
            1,
            expires_at - int(time.time()),
        )
        self.client.setex(
            f"{self.prefix}:{token_id}",
            ttl,
            "1",
        )

    def is_revoked(
        self,
        token_id: str,
        now: int | None = None,
    ) -> bool:
        return bool(
            self.client.exists(
                f"{self.prefix}:{token_id}"
            )
        )

def build_security_redis_client():
    import os
    from redis import Redis

    return Redis.from_url(
        os.getenv(
            "REDIS_URL",
            "redis://redis:6379/0",
        ),
        decode_responses=False,
    )
