from __future__ import annotations
from dataclasses import dataclass
import hashlib
import hmac
import json
import time

@dataclass(frozen=True)
class ApprovalVote:
    voter: str
    group: str
    approve: bool
    note: str
    created_at: int
    record_hash: str

@dataclass(frozen=True)
class QuorumPolicy:
    required_approvals: int
    required_groups: tuple[str, ...]
    expires_at: int

@dataclass(frozen=True)
class QuorumDecision:
    request_id: str
    approvals: int
    rejections: int
    groups: tuple[str, ...]
    quorum_met: bool
    rejected: bool
    status: str

class DuplicateVote(ValueError):
    pass

class QuorumPolicyError(ValueError):
    pass

class RedisQuorumApprovalRepository:
    VOTE_SCRIPT = '''
    local request_key = KEYS[1]
    local votes_key = KEYS[2]
    local voter_key = KEYS[3]
    local now = tonumber(ARGV[1])
    local vote_payload = ARGV[2]
    local voter = ARGV[3]

    local request_raw = redis.call("GET", request_key)
    if not request_raw then
        return {0, "missing"}
    end

    local request = cjson.decode(request_raw)
    if tonumber(request.expires_at) <= now then
        return {3, "expired"}
    end

    if redis.call("EXISTS", voter_key) == 1 then
        return {2, redis.call("GET", voter_key)}
    end

    redis.call("SET", voter_key, vote_payload)
    redis.call("SADD", votes_key, voter)
    redis.call("EXPIRE", voter_key, 86400)
    redis.call("EXPIRE", votes_key, 86400)
    return {1, vote_payload}
    '''

    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:maintenance:quorum",
        signing_secret: str,
    ):
        if len(signing_secret) < 16:
            raise ValueError("quorum signing secret en az 16 karakter olmalıdır")
        self.client = client
        self.prefix = prefix
        self.signing_secret = signing_secret.encode("utf-8")

    def initialize(
        self,
        *,
        request_id: str,
        required_approvals: int,
        required_groups: tuple[str, ...],
        expires_at: int,
    ) -> QuorumPolicy:
        if required_approvals <= 0:
            raise QuorumPolicyError("required_approvals pozitif olmalıdır")
        policy = QuorumPolicy(
            required_approvals=required_approvals,
            required_groups=tuple(sorted(set(required_groups))),
            expires_at=expires_at,
        )
        self.client.set(
            self._request_key(request_id),
            json.dumps(policy.__dict__, separators=(",", ":")),
        )
        return policy

    def cast_vote(
        self,
        *,
        request_id: str,
        voter: str,
        group: str,
        approve: bool,
        note: str,
        now: int | None = None,
    ) -> ApprovalVote:
        current = int(now if now is not None else time.time())
        payload = {
            "voter": voter,
            "group": group,
            "approve": bool(approve),
            "note": note[:1000],
            "created_at": current,
        }
        payload["record_hash"] = self._hash_payload(payload)
        encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))

        result = self.client.eval(
            self.VOTE_SCRIPT,
            3,
            self._request_key(request_id),
            self._votes_key(request_id),
            self._voter_key(request_id, voter),
            current,
            encoded,
            voter,
        )
        code = int(result[0])
        if code == 0:
            raise KeyError("Quorum talebi bulunamadı")
        if code == 2:
            raise DuplicateVote("Kullanıcı bu talep için daha önce oy kullandı")
        if code == 3:
            raise ValueError("Quorum talebinin süresi dolmuş")
        return ApprovalVote(**payload)

    def decision(
        self,
        request_id: str,
    ) -> QuorumDecision:
        policy = self._load_policy(request_id)
        votes = self.list_votes(request_id)
        approvals = [vote for vote in votes if vote.approve]
        rejections = [vote for vote in votes if not vote.approve]
        approval_groups = tuple(sorted({vote.group for vote in approvals}))

        required_groups_met = set(policy.required_groups).issubset(
            set(approval_groups)
        )
        quorum_met = (
            len(approvals) >= policy.required_approvals
            and required_groups_met
            and not rejections
        )
        rejected = bool(rejections)
        status = (
            "APPROVED"
            if quorum_met
            else "REJECTED"
            if rejected
            else "PENDING"
        )
        return QuorumDecision(
            request_id=request_id,
            approvals=len(approvals),
            rejections=len(rejections),
            groups=approval_groups,
            quorum_met=quorum_met,
            rejected=rejected,
            status=status,
        )

    def list_votes(
        self,
        request_id: str,
    ) -> tuple[ApprovalVote, ...]:
        voters = self.client.smembers(
            self._votes_key(request_id)
        )
        items = []
        for voter in voters:
            if isinstance(voter, bytes):
                voter = voter.decode("utf-8")
            payload = self.client.get(
                self._voter_key(request_id, str(voter))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            items.append(ApprovalVote(**data))
        return tuple(sorted(items, key=lambda item: item.created_at))

    def verify_votes(
        self,
        request_id: str,
    ) -> bool:
        for vote in self.list_votes(request_id):
            payload = dict(vote.__dict__)
            record_hash = payload.pop("record_hash")
            if not hmac.compare_digest(
                record_hash,
                self._hash_payload(payload),
            ):
                return False
        return True

    def _load_policy(
        self,
        request_id: str,
    ) -> QuorumPolicy:
        payload = self.client.get(
            self._request_key(request_id)
        )
        if payload is None:
            raise KeyError("Quorum talebi bulunamadı")
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        return QuorumPolicy(
            required_approvals=int(data["required_approvals"]),
            required_groups=tuple(data.get("required_groups") or ()),
            expires_at=int(data["expires_at"]),
        )

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

    def _request_key(self, request_id: str) -> str:
        return f"{self.prefix}:request:{request_id}"

    def _votes_key(self, request_id: str) -> str:
        return f"{self.prefix}:votes:{request_id}"

    def _voter_key(self, request_id: str, voter: str) -> str:
        return f"{self.prefix}:vote:{request_id}:{voter}"
