from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from .comeback_backtest import run_comeback_backtest
from .comeback_calibration import calibrate_thresholds
from .comeback_detector import evaluate_comeback
from .comeback_fixture_adapter import comeback_data_readiness, load_comeback_fixtures
from .comeback_scanner import scan_comeback_candidates


router = APIRouter(prefix="/api/comeback", tags=["HT/FT Comeback Detector"])


class ComebackEvaluateRequest(BaseModel):
    payload: dict[str, Any]
    alert_threshold: int = Field(default=75, ge=50, le=95)


class ComebackScanRequest(BaseModel):
    fixtures: list[dict[str, Any]]
    alert_threshold: int = Field(default=75, ge=50, le=95)
    min_similar_matches: int = Field(default=20, ge=1, le=500)
    limit: int = Field(default=10, ge=1, le=100)


@router.get("/health")
def comeback_health():
    return {
        "enabled": True,
        "markets": ["2/1", "1/2"],
        "default_alert_threshold": 75,
        "note": "Scores are ranking signals, not calibrated probabilities.",
    }


@router.post("/evaluate")
def comeback_evaluate(request: ComebackEvaluateRequest):
    return evaluate_comeback(
        request.payload,
        alert_threshold=request.alert_threshold,
    )


@router.post("/scan")
def comeback_scan(request: ComebackScanRequest):
    items = scan_comeback_candidates(
        request.fixtures,
        alert_threshold=request.alert_threshold,
        min_similar_matches=request.min_similar_matches,
        limit=request.limit,
    )
    return {
        "count": len(items),
        "threshold": request.alert_threshold,
        "items": items,
    }


@router.get("/stored-readiness")
def stored_comeback_readiness(
    hours: int = Query(default=36, ge=1, le=168),
):
    start = datetime.now(timezone.utc)
    fixtures = load_comeback_fixtures(
        start=start,
        end=start + timedelta(hours=hours),
        limit=1000,
    )
    return {
        "window_hours": hours,
        **comeback_data_readiness(fixtures),
    }


@router.get("/stored-candidates")
def stored_comeback_candidates(
    hours: int = Query(default=36, ge=1, le=168),
    alert_threshold: int = Query(default=75, ge=50, le=95),
    min_similar_matches: int = Query(default=20, ge=1, le=500),
    limit: int = Query(default=10, ge=1, le=100),
    use_calibrated_thresholds: bool = Query(default=True),
):
    start = datetime.now(timezone.utc)
    fixtures = load_comeback_fixtures(
        start=start,
        end=start + timedelta(hours=hours),
        limit=2000,
    )
    readiness = comeback_data_readiness(fixtures)

    calibration = None
    threshold_2_1 = alert_threshold
    threshold_1_2 = alert_threshold
    if use_calibrated_thresholds:
        backtest = run_comeback_backtest(lookback_days=1460, min_matches=100)
        calibration = calibrate_thresholds(
            backtest,
            default_threshold_2_1=alert_threshold,
            default_threshold_1_2=alert_threshold,
        )
        threshold_2_1 = int(calibration["2/1"]["threshold"])
        threshold_1_2 = int(calibration["1/2"]["threshold"])

    items = scan_comeback_candidates(
        fixtures,
        alert_threshold=alert_threshold,
        threshold_2_1=threshold_2_1,
        threshold_1_2=threshold_1_2,
        min_similar_matches=min_similar_matches,
        limit=limit,
    )
    return {
        "window_hours": hours,
        "threshold": alert_threshold,
        "thresholds": {"2/1": threshold_2_1, "1/2": threshold_1_2},
        "calibration": calibration,
        "readiness": readiness,
        "count": len(items),
        "items": items,
    }


@router.get("/backtest")
def comeback_backtest(
    lookback_days: int = Query(default=1460, ge=90, le=3650),
    min_matches: int = Query(default=100, ge=20, le=5000),
):
    result = run_comeback_backtest(
        lookback_days=lookback_days,
        min_matches=min_matches,
    )
    return {
        **result,
        "recommended_thresholds": calibrate_thresholds(result),
    }


def _self_check_payload(hours: int, lookback_days: int, min_matches: int, limit: int) -> dict[str, Any]:
    start = datetime.now(timezone.utc)
    fixtures = load_comeback_fixtures(
        start=start,
        end=start + timedelta(hours=hours),
        limit=2000,
    )
    readiness = comeback_data_readiness(fixtures)
    backtest = run_comeback_backtest(
        lookback_days=lookback_days,
        min_matches=min_matches,
    )
    calibration = calibrate_thresholds(backtest)
    threshold_2_1 = int(calibration["2/1"]["threshold"])
    threshold_1_2 = int(calibration["1/2"]["threshold"])
    items = scan_comeback_candidates(
        fixtures,
        alert_threshold=75,
        threshold_2_1=threshold_2_1,
        threshold_1_2=threshold_1_2,
        min_similar_matches=20,
        limit=limit,
    )
    ready = bool(backtest.get("enough_data")) and readiness.get("ready", 0) > 0
    return {
        "ready_for_live_use": ready,
        "window_hours": hours,
        "backtest": {
            "eligible_matches": backtest.get("eligible_matches", 0),
            "minimum_required": backtest.get("minimum_required", min_matches),
            "enough_data": backtest.get("enough_data", False),
            "baseline": backtest.get("baseline", {}),
        },
        "thresholds": {
            "2/1": threshold_2_1,
            "1/2": threshold_1_2,
        },
        "calibration": calibration,
        "readiness": readiness,
        "candidate_count": len(items),
        "top_candidates": items,
    }


@router.get("/self-check")
def comeback_self_check(
    hours: int = Query(default=36, ge=1, le=168),
    lookback_days: int = Query(default=1460, ge=90, le=3650),
    min_matches: int = Query(default=100, ge=20, le=5000),
    limit: int = Query(default=3, ge=1, le=20),
):
    return _self_check_payload(hours, lookback_days, min_matches, limit)


@router.get("/self-check.txt", response_class=PlainTextResponse)
def comeback_self_check_text(
    hours: int = Query(default=36, ge=1, le=168),
    lookback_days: int = Query(default=1460, ge=90, le=3650),
    min_matches: int = Query(default=100, ge=20, le=5000),
    limit: int = Query(default=3, ge=1, le=20),
):
    payload = _self_check_payload(hours, lookback_days, min_matches, limit)
    backtest = payload["backtest"]
    readiness = payload["readiness"]
    lines = [
        "ASLAN 2/1-1/2 MOTOR SELF CHECK",
        f"READY: {'YES' if payload['ready_for_live_use'] else 'NO'}",
        f"BACKTEST: {backtest['eligible_matches']}/{backtest['minimum_required']} eligible",
        f"THRESHOLDS: 2/1={payload['thresholds']['2/1']} | 1/2={payload['thresholds']['1/2']}",
        f"FIXTURES: {readiness.get('fixtures', 0)} | DATA READY: {readiness.get('ready', 0)}",
        f"HISTORY READY: {readiness.get('history_ready', 0)} | DIRECT HTFT: {readiness.get('direct_htft_ready', 0)}",
        f"PREDICTIONS: available={readiness.get('prediction_available', 0)} | items={readiness.get('prediction_items', 0)} | empty={readiness.get('prediction_empty', 0)} | errors={readiness.get('prediction_error_count', 0)}",
        f"CANDIDATES: {payload['candidate_count']}",
    ]
    for error in readiness.get("prediction_errors", ()):
        lines.append(
            f"PREDICTION ERROR x{error.get('count', 0)}: {error.get('error', '')}"
        )
    missing = readiness.get("missing_counts", {})
    if missing:
        lines.append(
            "MISSING: " + ", ".join(f"{key}={value}" for key, value in missing.items())
        )
    for index, item in enumerate(payload["top_candidates"], start=1):
        lines.append(
            f"{index}. {item.get('home_team')} - {item.get('away_team')} | "
            f"{item.get('preferred_market')} | score={item.get('score')} | "
            f"quality={item.get('quality_score')}"
        )
    return "\n".join(lines) + "\n"


@router.get("/threshold-guide")
def comeback_threshold_guide(
    threshold: int = Query(default=75, ge=50, le=95),
):
    return {
        "threshold": threshold,
        "bands": [
            {"min": 88, "label": "VERY_STRONG"},
            {"min": 82, "label": "STRONG"},
            {"min": threshold, "label": "WATCH"},
        ],
    }
