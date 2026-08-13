from __future__ import annotations
from dataclasses import dataclass

@dataclass(frozen=True)
class LeagueStrengthProfile:
    league_id: str
    mean_rating: float
    scale: float

class LeagueStrengthNormalizer:
    def normalize(self, rating: float, profile: LeagueStrengthProfile) -> float:
        if profile.scale <= 0:
            raise ValueError("Lig ölçeği pozitif olmalıdır")
        return (rating - profile.mean_rating) / profile.scale

    def denormalize(self, normalized_rating: float, profile: LeagueStrengthProfile) -> float:
        if profile.scale <= 0:
            raise ValueError("Lig ölçeği pozitif olmalıdır")
        return profile.mean_rating + normalized_rating * profile.scale

    def compare(
        self,
        home_rating: float,
        home_profile: LeagueStrengthProfile,
        away_rating: float,
        away_profile: LeagueStrengthProfile,
    ) -> float:
        return (
            self.normalize(home_rating, home_profile)
            - self.normalize(away_rating, away_profile)
        )
