from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json
import secrets
import time

@dataclass(frozen=True)
class QuarantineApprovalRequest:
    request_id: str
    claim_id: str
    requested_by: str
    note: str
    status: str
    created_at: int
    expires_at: int
    decided_by: str | None
    decided_at: int | None
    decision_note: str | None
    previous_hash: str
    record_hash: str

class ApprovalConflict(ValueError):
    pass

class ApprovalExpired(ValueError):
    pass

class RedisQuarantineApprovalRepository:
    DECIDE_SCRIPT = '''
    local request_key = KEYS[1]
    local current_raw = redis.call("GET", request_key)
    if not current_raw then
        return {0, "missing"}
    end

    local current = cjson.decode(current_raw)
    if current.status ~= "PENDING" then
        return {2, current_raw}
    end

    local now = tonumber(ARGV[1])
    if tonumber(current.expires_at) <= now then
        current.status = "EXPIRED"
        redis.call("SET", request_key, cjson.encode(current))
        return {3, cjson.encode(current)}
    end

    redis.call("SET", request_key, ARGV[2])
    return {1, ARGV[2]}
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:maintenance:approval",
        ttl_seconds: int = 1800,
        signing_secret: str,
    ):
        if ttl_seconds <= 0:
            raise ValueError("approval ttl pozitif olmalıdır")
        if len(signing_secret) < 16:
            raise ValueError("approval signing secret en az 16 karakter olmalıdır")
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds
        self.signing_secret = signing_secret.encode("utf-8")

    def create(
        self,
        *,
        claim_id: str,
        requested_by: str,
        note: str,
        now: int | None = None,
    ) -> QuarantineApprovalRequest:
        current = int(now if now is not None else time.time())
        request_id = secrets.token_urlsafe(18)
        previous_hash = self._latest_hash(claim_id)

        item = self._build(
            request_id=request_id,
            claim_id=claim_id,
            requested_by=requested_by,
            note=note,
            status="PENDING",
            created_at=current,
            expires_at=current + self.ttl_seconds,
            decided_by=None,
            decided_at=None,
            decision_note=None,
            previous_hash=previous_hash,
        )

        self.client.setex(
            self._request_key(request_id),
            self.ttl_seconds + 86400,
            self._serialize(item),
        )
        self.client.sadd(
            self._claim_index_key(claim_id),
            request_id,
        )
        self.client.expire(
            self._claim_index_key(claim_id),
            self.ttl_seconds + 86400,
        )
        self.client.set(
            self._latest_key(claim_id),
            item.record_hash,
        )
        return item

    def decide(
        self,
        *,
        request_id: str,
        decided_by: str,
        approve: bool,
        decision_note: str,
        now: int | None = None,
    ) -> QuarantineApprovalRequest:
        current = int(now if now is not None else time.time())
        existing = self.get(request_id)
        if existing is None:
            raise KeyError("Onay talebi bulunamadı")
        if existing.requested_by == decided_by:
            raise ApprovalConflict(
                "Talebi oluşturan kullanıcı kendi talebini onaylayamaz"
            )

        status = "APPROVED" if approve else "REJECTED"
        decided = self._build(
            request_id=existing.request_id,
            claim_id=existing.claim_id,
            requested_by=existing.requested_by,
            note=existing.note,
            status=status,
            created_at=existing.created_at,
            expires_at=existing.expires_at,
            decided_by=decided_by,
            decided_at=current,
            decision_note=decision_note,
            previous_hash=existing.record_hash,
        )

        result = self.client.eval(
            self.DECIDE_SCRIPT,
            1,
            self._request_key(request_id),
            current,
            self._serialize(decided),
        )
        code = int(result[0])

        if code == 0:
            raise KeyError("Onay talebi bulunamadı")
        if code == 3:
            raise ApprovalExpired("Onay talebinin süresi dolmuş")
        if code == 2:
            return self._deserialize(result[1])

        self.client.set(
            self._latest_key(existing.claim_id),
            decided.record_hash,
        )
        return decided

    def get(
        self,
        request_id: str,
    ) -> QuarantineApprovalRequest | None:
        payload = self.client.get(
            self._request_key(request_id)
        )
        if payload is None:
            return None
        return self._deserialize(payload)

    def list_claim(
        self,
        claim_id: str,
    ) -> tuple[QuarantineApprovalRequest, ...]:
        request_ids = self.client.smembers(
            self._claim_index_key(claim_id)
        )
        items = []
        for request_id in request_ids:
            if isinstance(request_id, bytes):
                request_id = request_id.decode("utf-8")
            item = self.get(str(request_id))
            if item is not None:
                items.append(item)
        return tuple(
            sorted(
                items,
                key=lambda item: item.created_at,
                reverse=True,
            )
        )

    def verify_chain(
        self,
        claim_id: str,
    ) -> bool:
        items = list(self.list_claim(claim_id))
        if not items:
            return True

        items.sort(key=lambda item: item.created_at)
        previous = ""
        for item in items:
            if item.previous_hash != previous:
                return False
            expected = self._hash_payload(
                self._payload_without_hash(item)
            )
            if not hmac.compare_digest(
                expected,
                item.record_hash,
            ):
                return False
            previous = item.record_hash
        return True

    def _build(
        self,
        *,
        request_id,
        claim_id,
        requested_by,
        note,
        status,
        created_at,
        expires_at,
        decided_by,
        decided_at,
        decision_note,
        previous_hash,
    ) -> QuarantineApprovalRequest:
        payload = {
            "request_id": request_id,
            "claim_id": claim_id,
            "requested_by": requested_by,
            "note": note[:1000],
            "status": status,
            "created_at": created_at,
            "expires_at": expires_at,
            "decided_by": decided_by,
            "decided_at": decided_at,
            "decision_note": (
                decision_note[:1000]
                if decision_note is not None
                else None
            ),
            "previous_hash": previous_hash,
        }
        return QuarantineApprovalRequest(
            **payload,
            record_hash=self._hash_payload(payload),
        )

    def _latest_hash(self, claim_id: str) -> str:
        value = self.client.get(
            self._latest_key(claim_id)
        )
        if value is None:
            return ""
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return str(value)

    def _hash_payload(self, payload: dict) -> str:
        canonical = json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
        return hmac.new(
            self.signing_secret,
            canonical,
            hashlib.sha256,
        ).hexdigest()

    @staticmethod
    def _payload_without_hash(
        item: QuarantineApprovalRequest,
    ) -> dict:
        data = dict(item.__dict__)
        data.pop("record_hash", None)
        return data

    @staticmethod
    def _serialize(
        item: QuarantineApprovalRequest,
    ) -> str:
        return json.dumps(
            item.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize(payload) -> QuarantineApprovalRequest:
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return QuarantineApprovalRequest(
            **json.loads(payload)
        )

    def _request_key(self, request_id: str) -> str:
        return f"{self.prefix}:request:{request_id}"

    def _claim_index_key(self, claim_id: str) -> str:
        return f"{self.prefix}:claim:{claim_id}"

    def _latest_key(self, claim_id: str) -> str:
        return f"{self.prefix}:latest:{claim_id}"
