from __future__ import annotations
from dataclasses import dataclass

from .domain import ProviderFixtureSnapshot

@dataclass(frozen=True)
class FixtureStateDecision:
    accepted: bool
    reason: str

class FixtureStateGuard:
    LIVE_STATES = {"LIVE", "INPLAY", "1ST_HALF", "2ND_HALF", "HT", "ET"}

    def evaluate(
        self,
        snapshot: ProviderFixtureSnapshot,
        previous: ProviderFixtureSnapshot | None,
    ) -> FixtureStateDecision:
        if snapshot.minute < 0 or snapshot.minute > 130:
            return FixtureStateDecision(False, "invalid_minute")
        if min(snapshot.home_score, snapshot.away_score) < 0:
            return FixtureStateDecision(False, "invalid_score")
        if snapshot.home_team_id == snapshot.away_team_id:
            return FixtureStateDecision(False, "same_team")
        if snapshot.state not in self.LIVE_STATES:
            return FixtureStateDecision(False, "fixture_not_live")

        if previous is not None:
            if snapshot.minute < previous.minute:
                return FixtureStateDecision(False, "stale_minute")
            if snapshot.home_score < previous.home_score:
                return FixtureStateDecision(False, "home_score_regression")
            if snapshot.away_score < previous.away_score:
                return FixtureStateDecision(False, "away_score_regression")

        return FixtureStateDecision(True, "accepted")
