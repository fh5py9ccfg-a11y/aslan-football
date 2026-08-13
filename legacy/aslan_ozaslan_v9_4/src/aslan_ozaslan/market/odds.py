from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class OddsSnapshot:
    captured_at: datetime
    home_odds: float
    draw_odds: float
    away_odds: float
    bookmaker: str

@dataclass(frozen=True)
class ImpliedProbabilities:
    home: float
    draw: float
    away: float
    overround: float

class MarketAnalyzer:
    def implied_probabilities(self, snapshot: OddsSnapshot) -> ImpliedProbabilities:
        odds = (snapshot.home_odds, snapshot.draw_odds, snapshot.away_odds)
        if any(value <= 1.0 for value in odds):
            raise ValueError("Ondalık oranlar 1.0'dan büyük olmalıdır")

        raw = [1.0 / value for value in odds]
        overround = sum(raw)
        normalized = [value / overround for value in raw]

        return ImpliedProbabilities(
            home=round(normalized[0], 6),
            draw=round(normalized[1], 6),
            away=round(normalized[2], 6),
            overround=round(overround - 1.0, 6),
        )

    def movement(self, first: OddsSnapshot, latest: OddsSnapshot) -> dict[str, float]:
        if latest.captured_at <= first.captured_at:
            raise ValueError("Son oran kaydı ilk kayıttan sonra olmalıdır")
        return {
            "home_change": round(latest.home_odds - first.home_odds, 4),
            "draw_change": round(latest.draw_odds - first.draw_odds, 4),
            "away_change": round(latest.away_odds - first.away_odds, 4),
        }
