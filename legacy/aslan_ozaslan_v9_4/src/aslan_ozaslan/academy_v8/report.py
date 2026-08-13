from __future__ import annotations

class AcademyNarrativeBuilder:
    def build(self, player, assessment) -> str:
        pathway_text = {
            "PROMOTE_TO_FIRST_TEAM": "A takıma yükseltilmesi öneriliyor.",
            "TRAIN_WITH_FIRST_TEAM": "A takımla düzenli antrenman öneriliyor.",
            "LOAN_FOR_DEVELOPMENT": "Rekabetçi dakika için kiralık gönderilmesi öneriliyor.",
            "HYBRID_DEVELOPMENT_PLAN": "Karma gelişim ve kontrollü kiralık planı öneriliyor.",
            "CONTINUE_ACADEMY": "Akademi programında gelişime devam etmesi öneriliyor.",
        }[assessment.pathway]

        return (
            f"{player.name} için {pathway_text} "
            f"A takım hazırlık skoru %{assessment.first_team_readiness * 100:.1f}, "
            f"12 aylık seviye projeksiyonu %{assessment.projected_level_12m * 100:.1f} "
            f"ve 24 aylık tahmini piyasa değeri "
            f"{assessment.projected_market_value_24m:,.0f}."
        )
