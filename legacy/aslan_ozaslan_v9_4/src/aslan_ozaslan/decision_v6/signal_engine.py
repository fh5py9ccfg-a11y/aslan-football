from __future__ import annotations

from .domain import DecisionContext, DecisionSignal

class LiveSignalEngine:
    def generate(
        self,
        context: DecisionContext,
    ) -> tuple[DecisionSignal, ...]:
        context.validate()
        signals = []

        score_edge = context.home_goals - context.away_goals
        card_edge = context.away_red_cards - context.home_red_cards
        probability_edge = context.home_probability - context.away_probability

        if probability_edge >= 0.18:
            signals.append(
                DecisionSignal(
                    signal_type="PROBABILITY_EDGE",
                    side="HOME",
                    strength=min(probability_edge, 1.0),
                    urgency="MEDIUM",
                    explanation="Ev sahibi kazanma olasılığı belirgin üstün.",
                )
            )
        elif probability_edge <= -0.18:
            signals.append(
                DecisionSignal(
                    signal_type="PROBABILITY_EDGE",
                    side="AWAY",
                    strength=min(abs(probability_edge), 1.0),
                    urgency="MEDIUM",
                    explanation="Deplasman kazanma olasılığı belirgin üstün.",
                )
            )

        if abs(context.momentum_edge) >= 1.0:
            side = "HOME" if context.momentum_edge > 0 else "AWAY"
            signals.append(
                DecisionSignal(
                    signal_type="MOMENTUM",
                    side=side,
                    strength=min(abs(context.momentum_edge) / 5.0, 1.0),
                    urgency="HIGH" if context.minute >= 70 else "MEDIUM",
                    explanation=f"{side} tarafı son bölümde momentum üstünlüğüne sahip.",
                )
            )

        if score_edge < 0 and context.minute >= 75:
            signals.append(
                DecisionSignal(
                    signal_type="LATE_COMEBACK_RISK",
                    side="HOME",
                    strength=min((context.minute - 70) / 20.0, 1.0),
                    urgency="HIGH",
                    explanation="Ev sahibi son bölümde geride ve risk seviyesi artıyor.",
                )
            )
        elif score_edge > 0 and context.minute >= 75:
            signals.append(
                DecisionSignal(
                    signal_type="LEAD_PROTECTION",
                    side="HOME",
                    strength=min(score_edge / 3.0, 1.0),
                    urgency="HIGH",
                    explanation="Ev sahibi skor avantajını koruma evresinde.",
                )
            )

        if card_edge != 0:
            advantaged = "HOME" if card_edge > 0 else "AWAY"
            signals.append(
                DecisionSignal(
                    signal_type="RED_CARD_ADVANTAGE",
                    side=advantaged,
                    strength=min(abs(card_edge) * 0.5, 1.0),
                    urgency="HIGH",
                    explanation=f"{advantaged} tarafı oyuncu sayısı avantajına sahip.",
                )
            )

        if context.reliability_score < 0.60:
            signals.append(
                DecisionSignal(
                    signal_type="LOW_RELIABILITY",
                    side="NEUTRAL",
                    strength=1.0 - context.reliability_score,
                    urgency="HIGH",
                    explanation="Model güvenilirliği düşük; karar ihtiyatla ele alınmalı.",
                )
            )

        return tuple(signals)
