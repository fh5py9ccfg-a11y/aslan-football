from dataclasses import dataclass
import json
import time

@dataclass(frozen=True)
class QuarantineDiagnostic:
    claim_id: str
    index_key: str
    phase: str
    exists: bool
    member_count: int
    orphan_members: int
    live_members: int
    index_ttl: int
    recommended_action: str
    checked_at: int
    error: str | None

class RedisQuarantineDiagnosticService:
    def __init__(
        self,
        client,
        *,
        session_prefix="aslan:refresh:session:",
        journal_prefix="aslan:maintenance:journal",
    ):
        self.client = client
        self.session_prefix = session_prefix
        self.journal_prefix = journal_prefix

    def inspect(self, claim_id, *, now=None):
        current = int(now if now is not None else time.time())
        raw = self.client.get(
            f"{self.journal_prefix}:quarantine:{claim_id}"
        )
        if raw is None:
            raise KeyError("Karantina kaydı bulunamadı")
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        item = json.loads(raw)
        index_key = str(item["index_key"])
        phase = str(item["phase"])

        try:
            exists = bool(self.client.exists(index_key))
            index_ttl = int(self.client.ttl(index_key))
            members = self.client.smembers(index_key) if exists else set()
            orphan = 0
            live = 0
            for member in members:
                if isinstance(member, bytes):
                    member = member.decode("utf-8")
                if int(self.client.ttl(
                    f"{self.session_prefix}{member}"
                )) > 0:
                    live += 1
                else:
                    orphan += 1

            recommendation = (
                "RETRY"
                if orphan > 0 or (live > 0 and index_ttl <= 0)
                else "RELEASE"
            )
            return QuarantineDiagnostic(
                claim_id=claim_id,
                index_key=index_key,
                phase=phase,
                exists=exists,
                member_count=len(members),
                orphan_members=orphan,
                live_members=live,
                index_ttl=index_ttl,
                recommended_action=recommendation,
                checked_at=current,
                error=None,
            )
        except Exception as exc:
            return QuarantineDiagnostic(
                claim_id=claim_id,
                index_key=index_key,
                phase=phase,
                exists=False,
                member_count=0,
                orphan_members=0,
                live_members=0,
                index_ttl=-2,
                recommended_action="HOLD",
                checked_at=current,
                error=str(exc),
            )
