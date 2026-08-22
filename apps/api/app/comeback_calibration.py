from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Mapping


@dataclass(frozen=True)
class MarketCalibration:
    market: str
    threshold: int
    selections: int
    hits: int
    hit_rate: float
    lift_vs_baseline: float | None
    source: str

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


def _choose_threshold(
    rows: list[Mapping[str, Any]],
    *,
    market: str,
    default_threshold: int,
    min_selections: int,
    min_lift: float,
) -> MarketCalibration:
    eligible = []
    for row in rows:
        try:
            threshold = int(row.get("threshold"))
            selections = int(row.get("selections"))
            hits = int(row.get("hits"))
            hit_rate = float(row.get("hit_rate"))
            lift_raw = row.get("lift_vs_baseline")
            lift = float(lift_raw) if lift_raw is not None else None
        except (TypeError, ValueError):
            continue
        if selections < min_selections:
            continue
        if lift is not None and lift < min_lift:
            continue
        eligible.append((lift or 0.0, hit_rate, selections, threshold, hits))

    if not eligible:
        return MarketCalibration(
            market=market,
            threshold=int(default_threshold),
            selections=0,
            hits=0,
            hit_rate=0.0,
            lift_vs_baseline=None,
            source="default_insufficient_backtest_support",
        )

    # Prefer strong lift, then realised hit-rate, then broader support.
    eligible.sort(key=lambda row: (row[0], row[1], row[2], row[3]), reverse=True)
    lift, hit_rate, selections, threshold, hits = eligible[0]
    return MarketCalibration(
        market=market,
        threshold=int(threshold),
        selections=int(selections),
        hits=int(hits),
        hit_rate=round(float(hit_rate), 4),
        lift_vs_baseline=round(float(lift), 3),
        source="backtest_calibrated",
    )


def calibrate_thresholds(
    backtest: Mapping[str, Any],
    *,
    default_threshold_2_1: int = 75,
    default_threshold_1_2: int = 75,
    min_selections: int = 25,
    min_lift: float = 1.20,
) -> dict[str, Any]:
    if not bool(backtest.get("enough_data")):
        result21 = MarketCalibration(
            "2/1", default_threshold_2_1, 0, 0, 0.0, None,
            "default_insufficient_backtest_data",
        )
        result12 = MarketCalibration(
            "1/2", default_threshold_1_2, 0, 0, 0.0, None,
            "default_insufficient_backtest_data",
        )
    else:
        thresholds = backtest.get("thresholds") or {}
        result21 = _choose_threshold(
            list(thresholds.get("2/1") or []),
            market="2/1",
            default_threshold=default_threshold_2_1,
            min_selections=min_selections,
            min_lift=min_lift,
        )
        result12 = _choose_threshold(
            list(thresholds.get("1/2") or []),
            market="1/2",
            default_threshold=default_threshold_1_2,
            min_selections=min_selections,
            min_lift=min_lift,
        )

    return {
        "2/1": result21.as_dict(),
        "1/2": result12.as_dict(),
        "policy": {
            "min_selections": int(min_selections),
            "min_lift": float(min_lift),
        },
    }
