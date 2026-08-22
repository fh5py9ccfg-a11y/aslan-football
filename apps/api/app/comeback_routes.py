from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from .comeback_detector import evaluate_comeback
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
