from __future__ import annotations
from dataclasses import dataclass
import json
import time

from .distributed_lease import StaleFencingToken

@dataclass(frozen=True)
class RemediationEvidence:
    claim_id: str
    index_key: str
    phase: str
    retry_status: str
    pre_orphans: int
    post_orphans: int
    pre_live: int
    post_live: int
    pre_ttl: int
    post_ttl: int
    verified: bool
    reason: str
    operator: str
    fencing_token: int
    created_at: int

class RedisRemediationEvidenceRepository:
    SAVE_SCRIPT = '''
    local evidence_key = KEYS[1]
    local fence_key = KEYS[2]
    local token = tonumber(ARGV[1])
    local payload = ARGV[2]
    local ttl = tonumber(ARGV[3])

    local current = tonumber(redis.call("GET", fence_key) or "0")
    if token < current then
        return {-1, current}
    end

    redis.call("SET", fence_key, token)
    redis.call("SET", evidence_key, payload, "EX", ttl)
    return {1, token}
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:maintenance:remediation",
        fence_key: str = "aslan:maintenance:session-index:fence",
        ttl_seconds: int = 2_592_000,
    ):
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds pozitif olmalıdır")
        self.client = client
        self.prefix = prefix
        self.fence_key = fence_key
        self.ttl_seconds = ttl_seconds

    def save(
        self,
        evidence: RemediationEvidence,
    ) -> None:
        payload = json.dumps(
            evidence.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        result = self.client.eval(
            self.SAVE_SCRIPT,
            2,
            self._key(evidence.claim_id),
            self.fence_key,
            evidence.fencing_token,
            payload,
            self.ttl_seconds,
        )
        if int(result[0]) == -1:
            raise StaleFencingToken(
                "Remediation evidence stale fencing token nedeniyle reddedildi"
            )

    def get(
        self,
        claim_id: str,
    ) -> RemediationEvidence | None:
        payload = self.client.get(self._key(claim_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        return RemediationEvidence(
            claim_id=str(data["claim_id"]),
            index_key=str(data["index_key"]),
            phase=str(data["phase"]),
            retry_status=str(data["retry_status"]),
            pre_orphans=int(data["pre_orphans"]),
            post_orphans=int(data["post_orphans"]),
            pre_live=int(data["pre_live"]),
            post_live=int(data["post_live"]),
            pre_ttl=int(data["pre_ttl"]),
            post_ttl=int(data["post_ttl"]),
            verified=bool(data["verified"]),
            reason=str(data["reason"]),
            operator=str(data["operator"]),
            fencing_token=int(data["fencing_token"]),
            created_at=int(data["created_at"]),
        )

    def _key(self, claim_id: str) -> str:
        return f"{self.prefix}:{claim_id}"

class QuarantineVerificationService:
    def __init__(
        self,
        *,
        diagnostic_service,
        retry_service,
        evidence_repository,
    ):
        self.diagnostic_service = diagnostic_service
        self.retry_service = retry_service
        self.evidence_repository = evidence_repository

    def retry_and_verify(
        self,
        *,
        claim_id: str,
        operator: str,
        fencing_token: int,
        now: int | None = None,
    ) -> RemediationEvidence:
        if fencing_token <= 0:
            raise ValueError("Aktif fencing token gerekli")
        current = int(now if now is not None else time.time())

        existing = self.evidence_repository.get(claim_id)
        if existing is not None and existing.verified:
            return existing

        before = self.diagnostic_service.inspect(
            claim_id,
            now=current,
        )
        retry = self.retry_service.retry(
            claim_id=claim_id,
            now=current,
        )
        after = self.diagnostic_service.inspect(
            claim_id,
            now=current,
        )

        verified, reason = self._verify(
            retry_status=retry.status,
            before=before,
            after=after,
        )
        evidence = RemediationEvidence(
            claim_id=claim_id,
            index_key=before.index_key,
            phase=before.phase,
            retry_status=retry.status,
            pre_orphans=before.orphan_members,
            post_orphans=after.orphan_members,
            pre_live=before.live_members,
            post_live=after.live_members,
            pre_ttl=before.index_ttl,
            post_ttl=after.index_ttl,
            verified=verified,
            reason=reason,
            operator=operator,
            fencing_token=fencing_token,
            created_at=current,
        )
        self.evidence_repository.save(evidence)
        return evidence

    @staticmethod
    def _verify(
        *,
        retry_status: str,
        before,
        after,
    ) -> tuple[bool, str]:
        if retry_status != "SUCCEEDED":
            return False, "Retry başarısız"
        if after.error:
            return False, "Retry sonrası tanılama başarısız"
        if after.orphan_members > 0:
            return False, "Orphan üyeler temizlenmedi"
        if (
            after.live_members > 0
            and after.index_ttl <= 0
        ):
            return False, "Canlı indeks TTL değeri geçersiz"
        if (
            after.member_count > before.member_count
        ):
            return False, "Retry sonrası üye sayısı beklenmedik biçimde arttı"
        return True, "Retry sonrası indeks sağlıklı"
