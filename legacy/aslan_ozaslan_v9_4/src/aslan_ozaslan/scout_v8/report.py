from __future__ import annotations

class ScoutNarrativeBuilder:
    def build(self, assessment) -> str:
        if assessment.recommendation == "PRIORITY_TARGET":
            lead = "Oyuncu öncelikli hedef olarak öne çıkıyor."
        elif assessment.recommendation == "SCOUT_DEEPLY":
            lead = "Oyuncu detaylı saha ve video takibini hak ediyor."
        elif assessment.recommendation == "MONITOR":
            lead = "Oyuncu izleme listesinde tutulmalı."
        else:
            lead = "Oyuncu mevcut koşullarda önerilmiyor."

        return (
            f"{lead} Kulüp uyumu %{assessment.club_fit_score * 100:.1f}, "
            f"24 aylık öngörülen seviye %{assessment.projected_level_24m * 100:.1f}, "
            f"lig geçiş skoru %{assessment.league_translation_score * 100:.1f}, "
            f"gizli yetenek skoru %{assessment.hidden_gem_score * 100:.1f} "
            f"ve toplam risk %{assessment.risk_score * 100:.1f}."
        )
