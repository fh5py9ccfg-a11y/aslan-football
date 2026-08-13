from __future__ import annotations

from .domain import WeaknessMap, MatchPlan

class MatchPlanGenerator:
    def generate(self, weakness: WeaknessMap) -> tuple[MatchPlan, ...]:
        zones = {
            "LEFT": weakness.left_defense,
            "RIGHT": weakness.right_defense,
            "CENTRAL": weakness.central_defense,
            "TRANSITION": weakness.transition_defense,
            "SET_PIECE": weakness.set_piece_defense,
        }
        primary_zone = max(zones, key=zones.get)

        plan_a = MatchPlan(
            name="PLAN_A",
            pressing_level=min(1.0, 0.60 + (1.0 - weakness.pressure_resistance) * 0.30),
            width=0.72 if primary_zone in {"LEFT", "RIGHT"} else 0.56,
            tempo=0.74,
            defensive_line=0.62,
            primary_zone=primary_zone,
            rationale=(
                f"Rakibin en zayıf alanı {primary_zone}.",
                "İlk bölümde kontrollü yüksek pres öneriliyor.",
            ),
        )
        plan_b = MatchPlan(
            name="PLAN_B",
            pressing_level=0.52,
            width=0.68,
            tempo=0.66,
            defensive_line=0.50,
            primary_zone=(
                "TRANSITION"
                if weakness.transition_defense >= 0.55
                else primary_zone
            ),
            rationale=(
                "Orta bloktan hızlı geçiş oyunu.",
                "Top kaybı sonrası kompakt kalma.",
            ),
        )
        plan_c = MatchPlan(
            name="PLAN_C",
            pressing_level=0.36,
            width=0.50,
            tempo=0.44,
            defensive_line=0.38,
            primary_zone="SET_PIECE",
            rationale=(
                "Skor avantajında risk azaltma.",
                "Duran toplardan kontrollü tehdit üretme.",
            ),
        )
        return (plan_a, plan_b, plan_c)
