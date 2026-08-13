from __future__ import annotations
from dataclasses import dataclass
import hashlib
import json
import secrets
import time
from threading import Lock

@dataclass(frozen=True)
class RefreshSession:
    session_id: str
    family_id: str
    subject: str
    roles: tuple[str, ...]
    secret_hash: str
    expires_at: int
    status: str
    rotation: int
    created_at: int
    last_used_at: int
    user_agent: str | None
    ip_address: str | None

class RefreshReuseDetected(ValueError):
    pass

class InMemoryRefreshSessionRepository:
    def __init__(self):
        self._items: dict[str, RefreshSession] = {}
        self._used_hashes: dict[str, set[str]] = {}
        self._family_index: dict[str, set[str]] = {}
        self._subject_index: dict[str, set[str]] = {}
        self._lock = Lock()

    @staticmethod
    def _hash(secret: str) -> str:
        return hashlib.sha256(
            secret.encode("utf-8")
        ).hexdigest()

    def issue(
        self,
        *,
        subject: str,
        roles: tuple[str, ...],
        ttl_seconds: int = 2_592_000,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, RefreshSession]:
        now = int(time.time())
        session_id = secrets.token_urlsafe(18)
        family_id = secrets.token_urlsafe(18)
        secret = secrets.token_urlsafe(32)
        session = RefreshSession(
            session_id=session_id,
            family_id=family_id,
            subject=subject,
            roles=tuple(roles),
            secret_hash=self._hash(secret),
            expires_at=now + ttl_seconds,
            status="ACTIVE",
            rotation=0,
            created_at=now,
            last_used_at=now,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        with self._lock:
            self._items[session_id] = session
            self._used_hashes[family_id] = set()
            self._family_index.setdefault(
                family_id,
                set(),
            ).add(session_id)
            self._subject_index.setdefault(
                subject,
                set(),
            ).add(session_id)

        return f"{session_id}.{secret}", session

    def rotate(
        self,
        refresh_token: str,
        *,
        now: int | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, RefreshSession]:
        current = int(now if now is not None else time.time())
        try:
            session_id, secret = refresh_token.split(".", 1)
        except ValueError as exc:
            raise ValueError("Refresh token biçimi geçersiz") from exc

        presented_hash = self._hash(secret)

        with self._lock:
            existing = self._items.get(session_id)
            if existing is None:
                raise ValueError("Refresh token geçersiz")

            used = self._used_hashes.setdefault(
                existing.family_id,
                set(),
            )
            if presented_hash in used:
                self._revoke_family_locked(existing.family_id)
                raise RefreshReuseDetected(
                    "Refresh token reuse tespit edildi; token ailesi iptal edildi"
                )

            if (
                existing.status != "ACTIVE"
                or existing.expires_at <= current
                or presented_hash != existing.secret_hash
            ):
                raise ValueError("Refresh token geçersiz")

            used.add(existing.secret_hash)
            new_secret = secrets.token_urlsafe(32)
            rotated = RefreshSession(
                session_id=existing.session_id,
                family_id=existing.family_id,
                subject=existing.subject,
                roles=existing.roles,
                secret_hash=self._hash(new_secret),
                expires_at=existing.expires_at,
                status="ACTIVE",
                rotation=existing.rotation + 1,
                created_at=existing.created_at,
                last_used_at=current,
                user_agent=user_agent or existing.user_agent,
                ip_address=ip_address or existing.ip_address,
            )
            self._items[session_id] = rotated

        return f"{session_id}.{new_secret}", rotated

    def get(
        self,
        session_id: str,
    ) -> RefreshSession | None:
        with self._lock:
            return self._items.get(session_id)

    def revoke(
        self,
        session_id: str,
    ) -> RefreshSession:
        with self._lock:
            existing = self._items.get(session_id)
            if existing is None:
                raise KeyError("Refresh session bulunamadı")
            revoked = RefreshSession(
                **{
                    **existing.__dict__,
                    "status": "REVOKED",
                }
            )
            self._items[session_id] = revoked
            return revoked

    def revoke_family(
        self,
        family_id: str,
    ) -> int:
        with self._lock:
            return self._revoke_family_locked(family_id)

    def revoke_subject(
        self,
        subject: str,
    ) -> int:
        count = 0
        with self._lock:
            for session_id in tuple(
                self._subject_index.get(
                    subject,
                    set(),
                )
            ):
                existing = self._items.get(session_id)
                if (
                    existing is not None
                    and existing.status == "ACTIVE"
                ):
                    self._items[session_id] = RefreshSession(
                        **{
                            **existing.__dict__,
                            "status": "REVOKED",
                        }
                    )
                    count += 1
        return count

    def list_subject(
        self,
        subject: str,
    ) -> tuple[RefreshSession, ...]:
        with self._lock:
            items = [
                self._items[session_id]
                for session_id in self._subject_index.get(
                    subject,
                    set(),
                )
                if session_id in self._items
            ]
        return tuple(
            sorted(
                items,
                key=lambda item: item.created_at,
                reverse=True,
            )
        )

    def _revoke_family_locked(
        self,
        family_id: str,
    ) -> int:
        count = 0
        for session_id in tuple(
            self._family_index.get(
                family_id,
                set(),
            )
        ):
            existing = self._items.get(session_id)
            if (
                existing is not None
                and existing.status == "ACTIVE"
            ):
                self._items[session_id] = RefreshSession(
                    **{
                        **existing.__dict__,
                        "status": "REVOKED",
                    }
                )
                count += 1
        return count

class RedisRefreshSessionRepository:
    ROTATE_SCRIPT = '''
    local session_key = KEYS[1]
    local used_key = KEYS[2]
    local family_key = KEYS[3]
    local presented_hash = ARGV[1]
    local new_hash = ARGV[2]
    local now = tonumber(ARGV[3])
    local user_agent = ARGV[4]
    local ip_address = ARGV[5]

    local raw = redis.call("GET", session_key)
    if not raw then
        return {"ERROR", "missing"}
    end

    local data = cjson.decode(raw)

    if redis.call("SISMEMBER", used_key, presented_hash) == 1 then
        local members = redis.call("SMEMBERS", family_key)
        for _, sid in ipairs(members) do
            local key = string.gsub(session_key, data.session_id, sid)
            local member_raw = redis.call("GET", key)
            if member_raw then
                local member = cjson.decode(member_raw)
                if member.status == "ACTIVE" then
                    member.status = "REVOKED"
                    redis.call("SET", key, cjson.encode(member))
                    redis.call("EXPIREAT", key, tonumber(member.expires_at))
                end
            end
        end
        return {"REUSE", data.family_id}
    end

    if data.status ~= "ACTIVE" then
        return {"ERROR", "inactive"}
    end

    if tonumber(data.expires_at) <= now then
        return {"ERROR", "expired"}
    end

    if data.secret_hash ~= presented_hash then
        return {"ERROR", "hash"}
    end

    redis.call("SADD", used_key, data.secret_hash)
    redis.call("EXPIRE", used_key, math.max(1, tonumber(data.expires_at) - now))

    data.secret_hash = new_hash
    data.rotation = tonumber(data.rotation) + 1
    data.last_used_at = now

    if user_agent ~= "" then
        data.user_agent = user_agent
    end

    if ip_address ~= "" then
        data.ip_address = ip_address
    end

    redis.call("SET", session_key, cjson.encode(data))
    redis.call("EXPIREAT", session_key, tonumber(data.expires_at))

    return {"OK", cjson.encode(data)}
    '''

    REVOKE_SET_SCRIPT = '''
    local index_key = KEYS[1]
    local session_prefix = ARGV[1]
    local members = redis.call("SMEMBERS", index_key)
    local count = 0

    for _, sid in ipairs(members) do
        local session_key = session_prefix .. sid
        local raw = redis.call("GET", session_key)
        if raw then
            local data = cjson.decode(raw)
            if data.status == "ACTIVE" then
                data.status = "REVOKED"
                redis.call("SET", session_key, cjson.encode(data))
                redis.call("EXPIREAT", session_key, tonumber(data.expires_at))
                count = count + 1
            end
        end
    end

    return count
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:refresh",
    ):
        self.client = client
        self.prefix = prefix

    @staticmethod
    def _hash(secret: str) -> str:
        return hashlib.sha256(
            secret.encode("utf-8")
        ).hexdigest()

    def _session_key(self, session_id: str) -> str:
        return f"{self.prefix}:session:{session_id}"

    def _session_prefix(self) -> str:
        return f"{self.prefix}:session:"

    def _used_key(self, family_id: str) -> str:
        return f"{self.prefix}:used:{family_id}"

    def _family_key(self, family_id: str) -> str:
        return f"{self.prefix}:family:{family_id}"

    def _subject_key(self, subject: str) -> str:
        return f"{self.prefix}:subject:{subject}"

    def issue(
        self,
        *,
        subject: str,
        roles: tuple[str, ...],
        ttl_seconds: int = 2_592_000,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, RefreshSession]:
        now = int(time.time())
        session_id = secrets.token_urlsafe(18)
        family_id = secrets.token_urlsafe(18)
        secret = secrets.token_urlsafe(32)
        session = RefreshSession(
            session_id=session_id,
            family_id=family_id,
            subject=subject,
            roles=tuple(roles),
            secret_hash=self._hash(secret),
            expires_at=now + ttl_seconds,
            status="ACTIVE",
            rotation=0,
            created_at=now,
            last_used_at=now,
            user_agent=user_agent,
            ip_address=ip_address,
        )

        pipeline = self.client.pipeline()
        pipeline.setex(
            self._session_key(session_id),
            ttl_seconds,
            self._serialize(session),
        )
        pipeline.sadd(
            self._subject_key(subject),
            session_id,
        )
        pipeline.expire(
            self._subject_key(subject),
            ttl_seconds,
        )
        pipeline.sadd(
            self._family_key(family_id),
            session_id,
        )
        pipeline.expire(
            self._family_key(family_id),
            ttl_seconds,
        )
        pipeline.execute()

        return f"{session_id}.{secret}", session

    def rotate(
        self,
        refresh_token: str,
        *,
        now: int | None = None,
        user_agent: str | None = None,
        ip_address: str | None = None,
    ) -> tuple[str, RefreshSession]:
        current = int(now if now is not None else time.time())
        try:
            session_id, secret = refresh_token.split(".", 1)
        except ValueError as exc:
            raise ValueError("Refresh token biçimi geçersiz") from exc

        existing = self.get(session_id)
        if existing is None:
            raise ValueError("Refresh token geçersiz")

        new_secret = secrets.token_urlsafe(32)
        result = self.client.eval(
            self.ROTATE_SCRIPT,
            3,
            self._session_key(session_id),
            self._used_key(existing.family_id),
            self._family_key(existing.family_id),
            self._hash(secret),
            self._hash(new_secret),
            current,
            user_agent or "",
            ip_address or "",
        )
        status = self._decode(result[0])
        payload = self._decode(result[1])

        if status == "REUSE":
            raise RefreshReuseDetected(
                "Refresh token reuse tespit edildi; token ailesi iptal edildi"
            )
        if status != "OK":
            raise ValueError("Refresh token geçersiz")

        session = self._deserialize(payload)
        return f"{session_id}.{new_secret}", session

    def get(
        self,
        session_id: str,
    ) -> RefreshSession | None:
        payload = self.client.get(
            self._session_key(session_id)
        )
        return (
            self._deserialize(payload)
            if payload is not None
            else None
        )

    def revoke(
        self,
        session_id: str,
    ) -> RefreshSession:
        existing = self.get(session_id)
        if existing is None:
            raise KeyError("Refresh session bulunamadı")

        revoked = RefreshSession(
            **{
                **existing.__dict__,
                "status": "REVOKED",
            }
        )
        self.client.set(
            self._session_key(session_id),
            self._serialize(revoked),
        )
        return revoked

    def revoke_family(
        self,
        family_id: str,
    ) -> int:
        return int(
            self.client.eval(
                self.REVOKE_SET_SCRIPT,
                1,
                self._family_key(family_id),
                self._session_prefix(),
            )
        )

    def revoke_subject(
        self,
        subject: str,
    ) -> int:
        return int(
            self.client.eval(
                self.REVOKE_SET_SCRIPT,
                1,
                self._subject_key(subject),
                self._session_prefix(),
            )
        )

    def list_subject(
        self,
        subject: str,
    ) -> tuple[RefreshSession, ...]:
        session_ids = self.client.smembers(
            self._subject_key(subject)
        )
        items = []

        for session_id in session_ids:
            session = self.get(
                self._decode(session_id)
            )
            if session is not None:
                items.append(session)

        return tuple(
            sorted(
                items,
                key=lambda item: item.created_at,
                reverse=True,
            )
        )

    def _serialize(
        self,
        session: RefreshSession,
    ) -> str:
        return json.dumps(
            {
                **session.__dict__,
                "roles": list(session.roles),
            },
            ensure_ascii=False,
            separators=(",", ":"),
        )

    def _deserialize(
        self,
        payload,
    ) -> RefreshSession:
        data = json.loads(
            self._decode(payload)
        )
        return RefreshSession(
            session_id=str(data["session_id"]),
            family_id=str(data["family_id"]),
            subject=str(data["subject"]),
            roles=tuple(
                str(item)
                for item in data.get("roles") or ()
            ),
            secret_hash=str(data["secret_hash"]),
            expires_at=int(data["expires_at"]),
            status=str(data["status"]),
            rotation=int(data["rotation"]),
            created_at=int(data["created_at"]),
            last_used_at=int(data["last_used_at"]),
            user_agent=(
                str(data["user_agent"])
                if data.get("user_agent")
                else None
            ),
            ip_address=(
                str(data["ip_address"])
                if data.get("ip_address")
                else None
            ),
        )

    @staticmethod
    def _decode(value) -> str:
        return (
            value.decode("utf-8")
            if isinstance(value, bytes)
            else str(value)
        )
