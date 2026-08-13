from dataclasses import dataclass

@dataclass(frozen=True)
class RotationRecommendation:
    rest_player_ids: tuple[str, ...]
    start_player_ids: tuple[str, ...]
    reason: str

class RotationAdvisor:
    def recommend(self, players, *, fatigue_threshold=.7):
        if not 0 <= fatigue_threshold <= 1:
            raise ValueError("Geçersiz eşik")
        rest = tuple(sorted(
            p.player_id for p in players
            if p.available and p.fatigue >= fatigue_threshold
        ))
        starters = tuple(
            p.player_id for p in sorted(
                [p for p in players if p.available and p.fatigue < fatigue_threshold],
                key=lambda p: (-p.value_score, p.fatigue, p.player_id)
            )
        )
        reason = "Yüksek yorgunluklu oyuncular dinlendirildi" if rest else "Zorunlu rotasyon ihtiyacı bulunmadı"
        return RotationRecommendation(rest, starters, reason)
