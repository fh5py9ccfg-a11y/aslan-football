from __future__ import annotations

class AgeCurveModel:
    def score(self, *, age: int, position: str) -> float:
        if not 15 <= age <= 45:
            raise ValueError("age geçersiz")

        peaks = {
            "GK": 29,
            "DF": 27,
            "MF": 26,
            "FW": 25,
        }
        peak = peaks.get(position.upper(), 26)
        distance = abs(age - peak)

        score = max(0.0, 1.0 - distance * 0.08)
        if age <= peak:
            score = min(1.0, score + 0.06)
        return score
