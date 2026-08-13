from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json
import time
from threading import Lock

@dataclass(frozen=True)
class ApiKeyRecord:
    key_id: str
    current_secret_hash: str
    previous_secret_hash: str | None
    previous_valid_until: int | None
    roles: tuple[str, ...]
    status: str
    version: int

    def public_dict(self) -> dict:
        return {
            "key_id": self.key_id,
            "roles": list(self.roles),
            "status": self.status,
            "version": self.version,
            "previous_valid_until": self.previous_valid_until,
        }

class InMemoryApiKeyRegistry:
    def __init__(self):
        self._items: dict[str, ApiKeyRecord] = {}
        self._lock = Lock()

    @staticmethod
    def hash_secret(secret: str) -> str:
        return hashlib.sha256(
            secret.encode("utf-8")
        ).hexdigest()

    def upsert(
        self,
        *,
        key_id: str,
        secret: str,
        roles: tuple[str, ...],
        status: str = "ACTIVE",
        version: int = 1,
    ) -> ApiKeyRecord:
        record = ApiKeyRecord(
            key_id=key_id,
            current_secret_hash=self.hash_secret(secret),
            previous_secret_hash=None,
            previous_valid_until=None,
            roles=tuple(roles),
            status=status,
            version=version,
        )
        with self._lock:
            self._items[key_id] = record
        return record

    def get(
        self,
        key_id: str,
    ) -> ApiKeyRecord | None:
        with self._lock:
            return self._items.get(key_id)

    def rotate(
        self,
        *,
        key_id: str,
        new_secret: str,
        grace_seconds: int = 0,
    ) -> ApiKeyRecord:
        if grace_seconds < 0:
            raise ValueError("grace_seconds negatif olamaz")
        with self._lock:
            existing = self._items.get(key_id)
            if existing is None:
                raise KeyError("API key bulunamadı")
            record = ApiKeyRecord(
                key_id=existing.key_id,
                current_secret_hash=self.hash_secret(new_secret),
                previous_secret_hash=(
                    existing.current_secret_hash
                    if grace_seconds > 0
                    else None
                ),
                previous_valid_until=(
                    int(time.time()) + grace_seconds
                    if grace_seconds > 0
                    else None
                ),
                roles=existing.roles,
                status="ACTIVE",
                version=existing.version + 1,
            )
            self._items[key_id] = record
            return record

    def revoke(
        self,
        key_id: str,
    ) -> ApiKeyRecord:
        with self._lock:
            existing = self._items.get(key_id)
            if existing is None:
                raise KeyError("API key bulunamadı")
            record = ApiKeyRecord(
                key_id=existing.key_id,
                current_secret_hash=existing.current_secret_hash,
                previous_secret_hash=None,
                previous_valid_until=None,
                roles=existing.roles,
                status="REVOKED",
                version=existing.version,
            )
            self._items[key_id] = record
            return record

    def verify(
        self,
        *,
        key_id: str,
        raw_secret: str,
        now: int | None = None,
    ) -> ApiKeyRecord:
        record = self.get(key_id)
        if record is None or record.status != "ACTIVE":
            raise ValueError("API key geçersiz")

        candidate = self.hash_secret(raw_secret)
        if hmac.compare_digest(
            candidate,
            record.current_secret_hash,
        ):
            return record

        current = int(now if now is not None else time.time())
        if (
            record.previous_secret_hash is not None
            and record.previous_valid_until is not None
            and current < record.previous_valid_until
            and hmac.compare_digest(
                candidate,
                record.previous_secret_hash,
            )
        ):
            return record

        raise ValueError("API key geçersiz")

    def list(self) -> tuple[ApiKeyRecord, ...]:
        with self._lock:
            return tuple(
                sorted(
                    self._items.values(),
                    key=lambda item: item.key_id,
                )
            )

class RedisApiKeyRegistry:
    ROTATE_SCRIPT = '''
    local payload = redis.call("GET", KEYS[1])
    if not payload then
        return false
    end
    return payload
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:api-key",
    ):
        self.client = client
        self.prefix = prefix

    @staticmethod
    def hash_secret(secret: str) -> str:
        return hashlib.sha256(
            secret.encode("utf-8")
        ).hexdigest()

    def _key(self, key_id: str) -> str:
        return f"{self.prefix}:{key_id}"

    def _serialize(
        self,
        record: ApiKeyRecord,
    ) -> str:
        return json.dumps(
            {
                "key_id": record.key_id,
                "current_secret_hash": record.current_secret_hash,
                "previous_secret_hash": record.previous_secret_hash,
                "previous_valid_until": record.previous_valid_until,
                "roles": list(record.roles),
                "status": record.status,
                "version": record.version,
            },
            separators=(",", ":"),
        )

    def _deserialize(
        self,
        payload,
    ) -> ApiKeyRecord:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        return ApiKeyRecord(
            key_id=str(data["key_id"]),
            current_secret_hash=str(
                data["current_secret_hash"]
            ),
            previous_secret_hash=(
                str(data["previous_secret_hash"])
                if data.get("previous_secret_hash")
                else None
            ),
            previous_valid_until=(
                int(data["previous_valid_until"])
                if data.get("previous_valid_until") is not None
                else None
            ),
            roles=tuple(
                str(item)
                for item in data.get("roles") or ()
            ),
            status=str(data["status"]),
            version=int(data["version"]),
        )

    def upsert(
        self,
        *,
        key_id: str,
        secret: str,
        roles: tuple[str, ...],
        status: str = "ACTIVE",
        version: int = 1,
    ) -> ApiKeyRecord:
        record = ApiKeyRecord(
            key_id=key_id,
            current_secret_hash=self.hash_secret(secret),
            previous_secret_hash=None,
            previous_valid_until=None,
            roles=tuple(roles),
            status=status,
            version=version,
        )
        self.client.set(
            self._key(key_id),
            self._serialize(record),
        )
        return record

    def get(
        self,
        key_id: str,
    ) -> ApiKeyRecord | None:
        payload = self.client.get(
            self._key(key_id)
        )
        return (
            self._deserialize(payload)
            if payload is not None
            else None
        )

    def rotate(
        self,
        *,
        key_id: str,
        new_secret: str,
        grace_seconds: int = 0,
    ) -> ApiKeyRecord:
        if grace_seconds < 0:
            raise ValueError("grace_seconds negatif olamaz")
        existing = self.get(key_id)
        if existing is None:
            raise KeyError("API key bulunamadı")

        record = ApiKeyRecord(
            key_id=existing.key_id,
            current_secret_hash=self.hash_secret(new_secret),
            previous_secret_hash=(
                existing.current_secret_hash
                if grace_seconds > 0
                else None
            ),
            previous_valid_until=(
                int(time.time()) + grace_seconds
                if grace_seconds > 0
                else None
            ),
            roles=existing.roles,
            status="ACTIVE",
            version=existing.version + 1,
        )
        self.client.set(
            self._key(key_id),
            self._serialize(record),
        )
        return record

    def revoke(
        self,
        key_id: str,
    ) -> ApiKeyRecord:
        existing = self.get(key_id)
        if existing is None:
            raise KeyError("API key bulunamadı")
        record = ApiKeyRecord(
            key_id=existing.key_id,
            current_secret_hash=existing.current_secret_hash,
            previous_secret_hash=None,
            previous_valid_until=None,
            roles=existing.roles,
            status="REVOKED",
            version=existing.version,
        )
        self.client.set(
            self._key(key_id),
            self._serialize(record),
        )
        return record

    def verify(
        self,
        *,
        key_id: str,
        raw_secret: str,
        now: int | None = None,
    ) -> ApiKeyRecord:
        record = self.get(key_id)
        if record is None or record.status != "ACTIVE":
            raise ValueError("API key geçersiz")

        candidate = self.hash_secret(raw_secret)
        if hmac.compare_digest(
            candidate,
            record.current_secret_hash,
        ):
            return record

        current = int(now if now is not None else time.time())
        if (
            record.previous_secret_hash is not None
            and record.previous_valid_until is not None
            and current < record.previous_valid_until
            and hmac.compare_digest(
                candidate,
                record.previous_secret_hash,
            )
        ):
            return record

        raise ValueError("API key geçersiz")

    def list(self) -> tuple[ApiKeyRecord, ...]:
        items = []
        cursor = 0
        while True:
            cursor, keys = self.client.scan(
                cursor=cursor,
                match=f"{self.prefix}:*",
                count=100,
            )
            for key in keys:
                key_value = (
                    key.decode("utf-8")
                    if isinstance(key, bytes)
                    else str(key)
                )
                record = self.get(
                    key_value.rsplit(":", 1)[-1]
                )
                if record is not None:
                    items.append(record)
            if int(cursor) == 0:
                break
        return tuple(
            sorted(
                items,
                key=lambda item: item.key_id,
            )
        )
