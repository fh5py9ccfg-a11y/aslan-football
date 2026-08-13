from __future__ import annotations

from .domain import DecisionContext
from .engine import RealTimeDecisionEngine
from .history import DecisionHistoryRepository

class LiveDecisionOrchestrator:
    def __init__(
        self,
        *,
        engine: RealTimeDecisionEngine,
        history: DecisionHistoryRepository,
    ):
        self.engine = engine
        self.history = history

    def on_live_state(
        self,
        *,
        fixture_id: str,
        live_state,
        momentum,
        reliability_score: float,
    ):
        context = DecisionContext(
            fixture_id=fixture_id,
            minute=live_state.minute,
            home_probability=live_state.home_probability,
            draw_probability=live_state.draw_probability,
            away_probability=live_state.away_probability,
            home_goals=live_state.home_goals,
            away_goals=live_state.away_goals,
            home_red_cards=live_state.home_red_cards,
            away_red_cards=live_state.away_red_cards,
            momentum_edge=momentum.net_momentum,
            reliability_score=reliability_score,
        )
        report = self.engine.evaluate(context)
        self.history.append(report)
        return report
