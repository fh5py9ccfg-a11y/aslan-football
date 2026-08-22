from __future__ import annotations

from typing import Any, Iterable, Mapping


def _type_name(item: Mapping[str, Any]) -> str:
    type_data = item.get("type")
    if isinstance(type_data, Mapping):
        return str(
            type_data.get("developer_name")
            or type_data.get("code")
            or type_data.get("name")
            or ""
        ).upper().replace("-", "_").replace(" ", "_")
    return ""


def _ratio(value: object) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number > 1.0:
        number /= 100.0
    if number < 0.0 or number > 1.0:
        return None
    return number


def _three_way(predictions: Mapping[str, Any]) -> tuple[float, float, float] | None:
    home = _ratio(predictions.get("home"))
    draw = _ratio(predictions.get("draw"))
    away = _ratio(predictions.get("away"))
    if home is None or draw is None or away is None:
        return None
    total = home + draw + away
    if total <= 0:
        return None
    return home / total, draw / total, away / total


def _extract_htft(predictions: Mapping[str, Any]) -> tuple[float | None, float | None]:
    normalized = {
        str(key).upper().replace(" ", "").replace("-", "/"): value
        for key, value in predictions.items()
    }
    score_21 = None
    score_12 = None
    for key, value in normalized.items():
        if key in {"2/1", "AWAY/HOME", "2_1"}:
            score_21 = _ratio(value)
        elif key in {"1/2", "HOME/AWAY", "1_2"}:
            score_12 = _ratio(value)
    return score_21, score_12


def sportmonks_predictions_to_comeback_inputs(
    items: Iterable[Mapping[str, Any]],
) -> dict[str, float]:
    result: dict[str, float] = {}

    for item in items:
        predictions = item.get("predictions")
        if not isinstance(predictions, Mapping):
            continue
        type_name = _type_name(item)

        if "FULLTIME_RESULT_PROBABILITY" in type_name and "1ST_HALF" not in type_name:
            values = _three_way(predictions)
            if values is not None:
                result["home_win_probability"], result["draw_probability"], result["away_win_probability"] = values

        elif (
            "FIRST_HALF_WINNER" in type_name
            or "FULLTIME_RESULT_1ST_HALF" in type_name
            or "1ST_HALF_RESULT" in type_name
        ):
            values = _three_way(predictions)
            if values is not None:
                (
                    result["first_half_home_probability"],
                    result["first_half_draw_probability"],
                    result["first_half_away_probability"],
                ) = values

        elif "HALF_TIME_FULL_TIME" in type_name or type_name.endswith("HT_FT_PROBABILITY"):
            score_21, score_12 = _extract_htft(predictions)
            if score_21 is not None:
                result["historical_2_1_rate"] = score_21
            if score_12 is not None:
                result["historical_1_2_rate"] = score_12

    return result
