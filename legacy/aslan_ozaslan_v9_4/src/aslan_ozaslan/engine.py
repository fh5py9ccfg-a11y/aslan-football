from __future__ import annotations

import hashlib
from .models import MatchInput, PredictionResult


class PredictionEngine:
    MIN_TEAM_SAMPLES = 4
    MIN_LEAGUE_SAMPLES = 20
    MAX_DATA_AGE_HOURS = 36
    ALLOWED_STATUSES = {"scheduled"}

    def predict(self, match: MatchInput) -> PredictionResult:
        self._validate_identifiers(match)

        if match.status not in self.ALLOWED_STATUSES:
            return self._blocked(match, "Maç durumu tahmine uygun değil.")

        if match.data_age_hours > self.MAX_DATA_AGE_HOURS:
            return self._blocked(match, "Veri güncel değil — model hesaplanmadı.")

        if not self._has_sufficient_data(match):
            return self._blocked(match, "Takıma özel veri yetersiz — model hesaplanmadı.")

        if None in (match.home_strength, match.away_strength, match.draw_tendency):
            return self._blocked(match, "Model girdileri eksik — tahmin üretilmedi.")

        home_raw = max(float(match.home_strength), 0.01)
        away_raw = max(float(match.away_strength), 0.01)
        draw_raw = max(float(match.draw_tendency), 0.01)
        total = home_raw + draw_raw + away_raw

        home = round(home_raw / total, 4)
        draw = round(draw_raw / total, 4)
        away = round(1.0 - home - draw, 4)

        confidence = min(
            100,
            int(40 + min(match.home_sample_count, 20) + min(match.away_sample_count, 20)
                + min(match.league_sample_count // 5, 20)),
        )

        return PredictionResult(
            status="OK", fixture_id=match.fixture_id,
            message="Tahmin maç verilerinden hesaplandı.",
            home_probability=home, draw_probability=draw, away_probability=away,
            data_confidence=confidence, calculation_id=self.calculation_id(match),
        )

    def cache_key(self, match: MatchInput, model_version: str = "v1-foundation") -> str:
        return f"prediction:{match.competition_id}:{match.season}:{match.fixture_id}:{model_version}"

    def calculation_id(self, match: MatchInput) -> str:
        raw = f"{self.cache_key(match)}:{match.home_team_id}:{match.away_team_id}"
        return hashlib.sha256(raw.encode()).hexdigest()[:16]

    def _blocked(self, match: MatchInput, message: str) -> PredictionResult:
        return PredictionResult(status="INSUFFICIENT_DATA", fixture_id=match.fixture_id,
                                message=message, data_confidence=0,
                                calculation_id=self.calculation_id(match))

    def _validate_identifiers(self, match: MatchInput) -> None:
        required = [match.fixture_id, match.competition_id, match.season,
                    match.home_team_id, match.away_team_id]
        if any(not value.strip() for value in required):
            raise ValueError("Maç ve takım kimlikleri zorunludur")
        if match.home_team_id == match.away_team_id:
            raise ValueError("Ev sahibi ve deplasman takımı aynı olamaz")

    def _has_sufficient_data(self, match: MatchInput) -> bool:
        return (match.home_sample_count >= self.MIN_TEAM_SAMPLES
                and match.away_sample_count >= self.MIN_TEAM_SAMPLES
                and match.league_sample_count >= self.MIN_LEAGUE_SAMPLES)
