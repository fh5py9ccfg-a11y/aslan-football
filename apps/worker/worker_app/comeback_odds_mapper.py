from __future__ import annotations

from collections import defaultdict
from statistics import median
from typing import Any, Iterable, Mapping


def _norm(value: object) -> str:
    return str(value or "").strip().upper().replace("-", " ").replace("_", " ")


def _odd(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 1.0 else None


def _is_fulltime(desc: str) -> bool:
    return desc in {"MATCH WINNER", "FULLTIME RESULT", "FULL TIME RESULT", "3 WAY RESULT"}


def _is_first_half(desc: str) -> bool:
    return "1ST HALF" in desc or "FIRST HALF" in desc or "HALF TIME RESULT" in desc or "HALFTIME RESULT" in desc


def _label(value: object) -> str | None:
    text = _norm(value)
    if text in {"1", "HOME", "HOME TEAM"}:
        return "home"
    if text in {"X", "DRAW"}:
        return "draw"
    if text in {"2", "AWAY", "AWAY TEAM"}:
        return "away"
    return None


def _three_way(rows: list[Mapping[str, Any]]) -> tuple[float, float, float] | None:
    by_bookmaker: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        side = _label(row.get("label") or row.get("name"))
        value = _odd(row.get("value"))
        if side and value:
            by_bookmaker[str(row.get("bookmaker_id") or "unknown")][side] = value

    normalized = []
    for values in by_bookmaker.values():
        if not all(key in values for key in ("home", "draw", "away")):
            continue
        raw = [1.0 / values["home"], 1.0 / values["draw"], 1.0 / values["away"]]
        total = sum(raw)
        if total > 0:
            normalized.append(tuple(value / total for value in raw))
    if not normalized:
        return None
    return tuple(median(row[index] for row in normalized) for index in range(3))


def sportmonks_odds_to_comeback_inputs(items: Iterable[Mapping[str, Any]]) -> dict[str, float]:
    fulltime: list[Mapping[str, Any]] = []
    first_half: list[Mapping[str, Any]] = []
    for item in items:
        desc = _norm(item.get("market_description") or (item.get("market") or {}).get("name"))
        if _is_first_half(desc):
            first_half.append(item)
        elif _is_fulltime(desc) or int(item.get("market_id") or 0) == 1:
            fulltime.append(item)

    result: dict[str, float] = {}
    ft = _three_way(fulltime)
    if ft:
        result.update(home_win_probability=ft[0], draw_probability=ft[1], away_win_probability=ft[2])
    ht = _three_way(first_half)
    if ht:
        result.update(first_half_home_probability=ht[0], first_half_draw_probability=ht[1], first_half_away_probability=ht[2])
    return result
