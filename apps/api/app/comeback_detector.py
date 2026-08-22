from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Mapping


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _norm_pct(value: float) -> float:
    """Accept either 0..1 ratios or 0..100 percentages."""
    value = float(value)
    if value > 1.0:
        value /= 100.0
    return _clamp(value)


@dataclass(frozen=True)
class ComebackInputs:
    # Match-result implied probabilities (vig-adjusted if possible).
    home_win_probability: float
    draw_probability: float
    away_win_probability: float

    # First-half implied probabilities.
    first_half_home_probability: float
    first_half_draw_probability: float
    first_half_away_probability: float

    # Team behavioural signals.
    home_comeback_rate_when_behind: float = 0.0
    away_comeback_rate_when_behind: float = 0.0
    home_loss_rate_when_ahead: float = 0.0
    away_loss_rate_when_ahead: float = 0.0

    # Goal timing: share of goals scored in second half.
    home_second_half_goal_share: float = 0.5
    away_second_half_goal_share: float = 0.5

    # Historical HT->FT pattern rates for the current/similar profile.
    historical_2_1_rate: float = 0.0
    historical_1_2_rate: float = 0.0

    # Similar-odds neighbour evidence. 0 means unavailable.
    similar_matches: int = 0
    similar_2_1_rate: float = 0.0
    similar_1_2_rate: float = 0.0

    # Optional market movement: positive means the named FT side shortened.
    home_ft_shortening: float = 0.0
    away_ft_shortening: float = 0.0


@dataclass(frozen=True)
class ComebackSignal:
    turnaround_potential: int
    score_2_1: int
    score_1_2: int
    label: str
    preferred_market: str | None
    reasons: tuple[str, ...]
    warnings: tuple[str, ...]

    def as_dict(self) -> dict:
        return asdict(self)


class ComebackDetector:
    """Ranks rare HT/FT reversals (2/1 and 1/2), not ordinary match winners.

    The detector deliberately combines independent evidence rather than using a
    single favourite/underdog rule. Scores are ranking signals (0..100), not
    calibrated probabilities.
    """

    def __init__(self, *, alert_threshold: int = 75, min_similar_matches: int = 20):
        self.alert_threshold = int(alert_threshold)
        self.min_similar_matches = int(min_similar_matches)

    @staticmethod
    def _favourite_gap(ft_side: float, fh_side: float) -> float:
        # Strong FT support without equally strong FH support is useful for a
        # comeback profile: the market likes the side over 90 minutes but not
        # necessarily from kickoff.
        return _clamp((ft_side - fh_side + 0.10) / 0.35)

    @staticmethod
    def _late_power(second_half_share: float) -> float:
        return _clamp((_norm_pct(second_half_share) - 0.45) / 0.30)

    @staticmethod
    def _movement(shortening: float) -> float:
        # Inputs can be fractional probability/price movement. Cap extreme
        # values because this is supporting evidence only.
        return _clamp(float(shortening) / 0.12)

    def evaluate(self, inputs: ComebackInputs) -> ComebackSignal:
        hp = _norm_pct(inputs.home_win_probability)
        ap = _norm_pct(inputs.away_win_probability)
        fhh = _norm_pct(inputs.first_half_home_probability)
        fha = _norm_pct(inputs.first_half_away_probability)

        home_comeback = _norm_pct(inputs.home_comeback_rate_when_behind)
        away_comeback = _norm_pct(inputs.away_comeback_rate_when_behind)
        home_blown_lead = _norm_pct(inputs.home_loss_rate_when_ahead)
        away_blown_lead = _norm_pct(inputs.away_loss_rate_when_ahead)

        hist21 = _norm_pct(inputs.historical_2_1_rate)
        hist12 = _norm_pct(inputs.historical_1_2_rate)
        sim21 = _norm_pct(inputs.similar_2_1_rate)
        sim12 = _norm_pct(inputs.similar_1_2_rate)

        neighbour_weight = _clamp(inputs.similar_matches / max(self.min_similar_matches, 1))

        # 2/1 = away leads at HT, home wins FT.
        score21 = 100.0 * (
            0.22 * self._favourite_gap(hp, fhh)
            + 0.20 * home_comeback
            + 0.16 * away_blown_lead
            + 0.12 * self._late_power(inputs.home_second_half_goal_share)
            + 0.10 * _clamp(fha / 0.45)
            + 0.08 * _clamp(hist21 / 0.18)
            + 0.09 * neighbour_weight * _clamp(sim21 / 0.18)
            + 0.03 * self._movement(inputs.home_ft_shortening)
        )

        # 1/2 = home leads at HT, away wins FT.
        score12 = 100.0 * (
            0.22 * self._favourite_gap(ap, fha)
            + 0.20 * away_comeback
            + 0.16 * home_blown_lead
            + 0.12 * self._late_power(inputs.away_second_half_goal_share)
            + 0.10 * _clamp(fhh / 0.45)
            + 0.08 * _clamp(hist12 / 0.18)
            + 0.09 * neighbour_weight * _clamp(sim12 / 0.18)
            + 0.03 * self._movement(inputs.away_ft_shortening)
        )

        score21_i = int(round(_clamp(score21 / 100.0) * 100))
        score12_i = int(round(_clamp(score12 / 100.0) * 100))
        top = max(score21_i, score12_i)
        turnaround = int(round(0.65 * top + 0.35 * min(100, score21_i + score12_i)))

        preferred = "2/1" if score21_i >= score12_i else "1/2"
        preferred_score = max(score21_i, score12_i)
        if preferred_score < self.alert_threshold:
            preferred_market = None
            label = "NO_ALERT"
        elif preferred_score >= 88:
            preferred_market = preferred
            label = "VERY_STRONG"
        elif preferred_score >= 82:
            preferred_market = preferred
            label = "STRONG"
        else:
            preferred_market = preferred
            label = "WATCH"

        reasons: list[str] = []
        if score21_i >= self.alert_threshold:
            reasons.append("Home side has a 2/1 reversal profile: FT support + comeback/late-goal evidence.")
        if score12_i >= self.alert_threshold:
            reasons.append("Away side has a 1/2 reversal profile: FT support + comeback/late-goal evidence.")
        if inputs.similar_matches >= self.min_similar_matches:
            reasons.append(
                f"Similar-odds evidence included from {int(inputs.similar_matches)} historical matches."
            )
        if not reasons:
            reasons.append("No reversal pattern clears the configured alert threshold.")

        warnings: list[str] = [
            "2/1 and 1/2 are rare outcomes; detector scores are ranking signals, not guarantees."
        ]
        if inputs.similar_matches < self.min_similar_matches:
            warnings.append("Similar-match sample is small; neighbour evidence was down-weighted.")

        return ComebackSignal(
            turnaround_potential=turnaround,
            score_2_1=score21_i,
            score_1_2=score12_i,
            label=label,
            preferred_market=preferred_market,
            reasons=tuple(reasons),
            warnings=tuple(warnings),
        )


def evaluate_comeback(payload: Mapping[str, object], *, alert_threshold: int = 75) -> dict:
    """Small integration helper for API/service layers."""
    detector = ComebackDetector(alert_threshold=alert_threshold)
    inputs = ComebackInputs(**dict(payload))
    return detector.evaluate(inputs).as_dict()
