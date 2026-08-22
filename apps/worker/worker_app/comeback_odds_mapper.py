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


def _market_text(item: Mapping[str, Any]) -> str:
    market = item.get("market") or {}
    name = market.get("name") if isinstance(market, Mapping) else None
    desc = item.get("market_description") or item.get("market_name") or name or ""
    return _norm(desc)


def _period_text(item: Mapping[str, Any]) -> str:
    period = item.get("period") or item.get("scope") or item.get("timeframe") or ""
    return _norm(period)


def _is_fulltime(desc: str, period: str = "") -> bool:
    tokens = {
        "MATCH WINNER", "FULLTIME RESULT", "FULL TIME RESULT", "3 WAY RESULT",
        "1X2", "MATCH RESULT", "FINAL RESULT", "REGULAR TIME RESULT",
    }
    if desc in tokens:
        return True
    if "FULL TIME" in desc or "FULLTIME" in desc or "MATCH RESULT" in desc:
        return True
    if desc == "RESULT" and period in {"FULL TIME", "FULLTIME", "MATCH"}:
        return True
    return False


def _is_first_half(desc: str, period: str = "") -> bool:
    markers = (
        "1ST HALF", "FIRST HALF", "HALF TIME RESULT", "HALFTIME RESULT",
        "1ST HALF RESULT", "FIRST HALF RESULT", "HALF TIME 1X2", "HT RESULT",
    )
    if any(marker in desc for marker in markers):
        return True
    if desc in {"1X2", "RESULT", "3 WAY RESULT"} and period in {
        "1ST HALF", "FIRST HALF", "HALF TIME", "HALFTIME", "HT"
    }:
        return True
    return False


def _label(value: object) -> str | None:
    text = _norm(value)
    if text in {"1", "HOME", "HOME TEAM", "HOME WIN", "TEAM 1"}:
        return "home"
    if text in {"X", "DRAW", "TIE"}:
        return "draw"
    if text in {"2", "AWAY", "AWAY TEAM", "AWAY WIN", "TEAM 2"}:
        return "away"
    return None


def _row_label(row: Mapping[str, Any]) -> str | None:
    candidate = (
        row.get("label") or row.get("name") or row.get("selection") or
        row.get("selection_name") or row.get("participant")
    )
    side = _label(candidate)
    if side:
        return side
    outcome = row.get("outcome")
    if isinstance(outcome, Mapping):
        return _label(outcome.get("name") or outcome.get("label"))
    return None


def _row_odd(row: Mapping[str, Any]) -> float | None:
    for key in ("value", "odd", "odds", "decimal", "price"):
        value = _odd(row.get(key))
        if value:
            return value
    return None


def _bookmaker_key(row: Mapping[str, Any]) -> str:
    bookmaker = row.get("bookmaker")
    if isinstance(bookmaker, Mapping):
        return str(bookmaker.get("id") or bookmaker.get("name") or "unknown")
    return str(row.get("bookmaker_id") or row.get("bookmaker_name") or "unknown")


def _three_way(rows: list[Mapping[str, Any]]) -> tuple[float, float, float] | None:
    by_bookmaker: dict[str, dict[str, float]] = defaultdict(dict)
    for row in rows:
        side = _row_label(row)
        value = _row_odd(row)
        if side and value:
            by_bookmaker[_bookmaker_key(row)][side] = value

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
        desc = _market_text(item)
        period = _period_text(item)
        market_id = int(item.get("market_id") or (item.get("market") or {}).get("id") or 0)
        if _is_first_half(desc, period):
            first_half.append(item)
        elif _is_fulltime(desc, period) or market_id == 1:
            fulltime.append(item)

    result: dict[str, float] = {}
    ft = _three_way(fulltime)
    if ft:
        result.update(home_win_probability=ft[0], draw_probability=ft[1], away_win_probability=ft[2])
    ht = _three_way(first_half)
    if ht:
        result.update(first_half_home_probability=ht[0], first_half_draw_probability=ht[1], first_half_away_probability=ht[2])
    return result
