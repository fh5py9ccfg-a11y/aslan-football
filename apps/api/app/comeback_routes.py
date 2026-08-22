from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

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
):
    start = datetime.now(timezone.utc)
    fixtures = load_comeback_fixtures(
        start=start,
        end=start + timedelta(hours=hours),
        limit=2000,
    )
    readiness = comeback_data_readiness(fixtures)
    items = scan_comeback_candidates(
        fixtures,
        alert_threshold=alert_threshold,
        min_similar_matches=min_similar_matches,
        limit=limit,
    )
    return {
        "window_hours": hours,
        "threshold": alert_threshold,
        "readiness": readiness,
        "count": len(items),
        "items": items,
    }


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
