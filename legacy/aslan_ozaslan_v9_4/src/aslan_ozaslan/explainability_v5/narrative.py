from __future__ import annotations

from .domain import NormalizedFactor

class FootballNarrativeBuilder:
    OUTCOME_LABELS = {
        "HOME": "ev sahibi galibiyeti",
        "DRAW": "beraberlik",
        "AWAY": "deplasman galibiyeti",
    }

    def build(
        self,
        *,
        outcome: str,
        probability: float,
        factors: tuple[NormalizedFactor, ...],
        reliability_label: str,
    ) -> str:
        if outcome not in self.OUTCOME_LABELS:
            raise ValueError("Geçersiz sonuç etiketi")
        if not 0 <= probability <= 1:
            raise ValueError("probability geçersiz")

        positives = [
            factor for factor in factors
            if factor.signed_share > 0
        ][:3]
        negatives = [
            factor for factor in factors
            if factor.signed_share < 0
        ][:2]

        positive_text = ", ".join(
            f"{factor.name} (%{factor.absolute_share * 100:.1f})"
            for factor in positives
        ) or "belirgin pozitif faktör bulunmaması"

        if negatives:
            negative_text = ", ".join(
                f"{factor.name} (-%{factor.absolute_share * 100:.1f})"
                for factor in negatives
            )
            contrast = (
                f" Buna karşılık {negative_text} tahmin gücünü azaltıyor."
            )
        else:
            contrast = ""

        return (
            f"Model {self.OUTCOME_LABELS[outcome]} olasılığını "
            f"%{probability * 100:.1f} olarak hesaplıyor. "
            f"Başlıca destekleyici faktörler {positive_text}.{contrast} "
            f"Genel güvenilirlik seviyesi {reliability_label}."
        )
