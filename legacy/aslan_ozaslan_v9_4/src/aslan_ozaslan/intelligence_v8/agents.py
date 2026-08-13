from __future__ import annotations

from .domain import TacticalRecommendationContext, AgentOpinion

class TacticalAgent:
    name = "tactical_agent"

    def evaluate(self, context: TacticalRecommendationContext) -> AgentOpinion:
        context.validate()

        if context.goal_difference < 0 and context.minute >= 70:
            action = "INCREASE_PRESSING"
            confidence = 0.82
            risk = 0.62
            rationale = "Maçın son bölümünde geride olunduğu için pres yoğunluğu artırılmalı."
        elif context.goal_difference > 0 and context.minute >= 75:
            action = "LOWER_DEFENSIVE_BLOCK"
            confidence = 0.78
            risk = 0.32
            rationale = "Skor avantajını korumak için savunma bloğu kontrollü biçimde geriye çekilmeli."
        elif context.momentum_edge < -1.5:
            action = "REDUCE_TEMPO"
            confidence = 0.70
            risk = 0.28
            rationale = "Rakip momentumunu kırmak için tempo düşürülmeli."
        else:
            action = "MAINTAIN_SHAPE"
            confidence = 0.66
            risk = 0.18
            rationale = "Mevcut taktik yapı dengeli görünüyor."

        return AgentOpinion(self.name, action, confidence, risk, rationale)

class PerformanceAgent:
    name = "performance_agent"

    def evaluate(self, context: TacticalRecommendationContext) -> AgentOpinion:
        context.validate()

        if context.fatigue_level >= 0.75:
            action = "MAKE_SUBSTITUTION"
            confidence = 0.86
            risk = 0.20
            rationale = "Yüksek yorgunluk seviyesi performans düşüşü ve hata riskini artırıyor."
        elif context.fatigue_level >= 0.55:
            action = "REDUCE_PRESSING"
            confidence = 0.74
            risk = 0.24
            rationale = "Orta-yüksek yorgunluk nedeniyle pres yoğunluğu kontrollü azaltılmalı."
        else:
            action = "MAINTAIN_INTENSITY"
            confidence = 0.68
            risk = 0.16
            rationale = "Fiziksel yük sürdürülebilir seviyede."

        return AgentOpinion(self.name, action, confidence, risk, rationale)

class RiskAgent:
    name = "risk_agent"

    def evaluate(self, context: TacticalRecommendationContext) -> AgentOpinion:
        context.validate()

        if context.reliability_score < 0.60:
            return AgentOpinion(
                self.name,
                "MANUAL_REVIEW",
                0.90,
                0.10,
                "Model güvenilirliği düşük; otomatik taktik öneri yerine manuel inceleme gerekli.",
            )

        attacking_risk = (
            context.pressing * 0.35
            + context.defensive_line * 0.35
            + context.tempo * 0.30
        )

        if attacking_risk >= 0.75 and context.goal_difference >= 0:
            return AgentOpinion(
                self.name,
                "REDUCE_RISK",
                0.80,
                0.22,
                "Mevcut oyun riski skor durumuna göre gereğinden yüksek.",
            )

        return AgentOpinion(
            self.name,
            "RISK_ACCEPTABLE",
            0.72,
            0.15,
            "Mevcut taktik risk kabul edilebilir seviyede.",
        )
