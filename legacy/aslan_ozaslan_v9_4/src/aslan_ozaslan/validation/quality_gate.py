from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from aslan_ozaslan.domain import FixtureRecord, TeamSnapshot


@dataclass(frozen=True)
class QualityDecision:
    accepted: bool
    score: int
    reasons: tuple[str, ...]


class DataQualityGate:
    ALLOWED_FIXTURE_STATUS = {"SCHEDULED", "TIMED"}

    def __init__(self, *, max_snapshot_age_hours: int = 24, min_matches: int = 4):
        self.max_snapshot_age_hours = max_snapshot_age_hours
        self.min_matches = min_matches

    def evaluate(
        self,
        *,
        fixture: FixtureRecord,
        home: TeamSnapshot,
        away: TeamSnapshot,
        now: datetime | None = None,
    ) -> QualityDecision:
        current = now or datetime.now(timezone.utc)
        reasons: list[str] = []
        score = 100

        if fixture.status not in self.ALLOWED_FIXTURE_STATUS:
            reasons.append("Maç durumu tahmin üretimine uygun değil")
            score -= 50
        if home.team_id != fixture.home_team_id or away.team_id != fixture.away_team_id:
            reasons.append("Takım kimliği ile fikstür eşleşmiyor")
            score -= 100
        if home.competition_id != fixture.competition_id or away.competition_id != fixture.competition_id:
            reasons.append("Takım verisi yanlış organizasyona ait")
            score -= 40
        if home.matches_played < self.min_matches or away.matches_played < self.min_matches:
            reasons.append("Takıma özel örnek sayısı yetersiz")
            score -= 40

        max_age = timedelta(hours=self.max_snapshot_age_hours)
        if current - home.observed_at > max_age or current - away.observed_at > max_age:
            reasons.append("Takım verisi güncel değil")
            score -= 40
        if not home.injuries_known or not away.injuries_known:
            reasons.append("Sakatlık bilgisi eksik")
            score -= 10
        if not home.lineup_known or not away.lineup_known:
            reasons.append("Muhtemel kadro bilgisi eksik")
            score -= 10

        score = max(0, score)
        blocking = {
            "Maç durumu tahmin üretimine uygun değil",
            "Takım kimliği ile fikstür eşleşmiyor",
            "Takım verisi yanlış organizasyona ait",
            "Takıma özel örnek sayısı yetersiz",
            "Takım verisi güncel değil",
        }
        accepted = not any(reason in blocking for reason in reasons)
        return QualityDecision(accepted=accepted, score=score, reasons=tuple(reasons))
