from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class QuorumRiskPolicy:
    level: str
    score: int
    required_approvals: int
    required_groups: tuple[str, ...]
    reasons: tuple[str, ...]

class QuorumRiskPolicyEngine:
    def evaluate(
        self,
        *,
        orphan_members: int,
        live_members: int,
        index_ttl: int,
        attempts: int,
        phase: str,
    ) -> QuorumRiskPolicy:
        score = 0
        reasons = []

        if orphan_members >= 100:
            score += 3
            reasons.append("yüksek orphan sayısı")
        elif orphan_members > 0:
            score += 1
            reasons.append("orphan üyeler mevcut")

        if live_members >= 1000:
            score += 3
            reasons.append("çok yüksek canlı session etkisi")
        elif live_members >= 100:
            score += 2
            reasons.append("yüksek canlı session etkisi")
        elif live_members > 0:
            score += 1
            reasons.append("canlı session etkisi")

        if live_members > 0 and index_ttl <= 0:
            score += 2
            reasons.append("geçersiz indeks TTL")

        if attempts >= 5:
            score += 2
            reasons.append("çoklu başarısız retry")
        elif attempts >= 3:
            score += 1
            reasons.append("tekrarlanan başarısız retry")

        if phase == "family":
            score += 1
            reasons.append("token family kapsamı")

        if score >= 7:
            return QuorumRiskPolicy(
                level="CRITICAL",
                score=score,
                required_approvals=3,
                required_groups=("admin", "security", "ops"),
                reasons=tuple(reasons),
            )
        if score >= 4:
            return QuorumRiskPolicy(
                level="HIGH",
                score=score,
                required_approvals=2,
                required_groups=("admin", "security"),
                reasons=tuple(reasons),
            )
        if score >= 2:
            return QuorumRiskPolicy(
                level="MEDIUM",
                score=score,
                required_approvals=2,
                required_groups=("admin",),
                reasons=tuple(reasons),
            )
        return QuorumRiskPolicy(
            level="LOW",
            score=score,
            required_approvals=1,
            required_groups=("admin",),
            reasons=tuple(reasons),
        )
