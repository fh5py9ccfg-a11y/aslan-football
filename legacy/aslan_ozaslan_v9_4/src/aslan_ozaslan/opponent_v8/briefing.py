from __future__ import annotations

class MatchBriefingBuilder:
    def build(
        self,
        *,
        opponent_id: str,
        weakness,
        matchups,
        plans,
        simulation,
    ) -> str:
        strongest_weakness = max(
            {
                "sol savunma": weakness.left_defense,
                "sağ savunma": weakness.right_defense,
                "merkez savunma": weakness.central_defense,
                "geçiş savunması": weakness.transition_defense,
                "duran top savunması": weakness.set_piece_defense,
            },
            key=lambda key: {
                "sol savunma": weakness.left_defense,
                "sağ savunma": weakness.right_defense,
                "merkez savunma": weakness.central_defense,
                "geçiş savunması": weakness.transition_defense,
                "duran top savunması": weakness.set_piece_defense,
            }[key],
        )

        matchup_text = (
            ", ".join(matchups)
            if matchups
            else "Belirgin bireysel eşleşme avantajı yok."
        )
        return (
            f"{opponent_id} için ana hedef bölge {strongest_weakness}. "
            f"Önerilen başlangıç planı {plans[0].name}; ana hücum bölgesi "
            f"{plans[0].primary_zone}. Kritik eşleşmeler: {matchup_text}. "
            f"Simülasyonda beklenen gol {simulation.expected_goals_for:.2f}, "
            f"yenme ihtimali için ilk gol olasılığı "
            f"%{simulation.first_goal_probability * 100:.1f}."
        )
