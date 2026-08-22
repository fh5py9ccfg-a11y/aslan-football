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
    payload: dict[str, Any]; alert_threshold: int = Field(default=75, ge=50, le=95)
class ComebackScanRequest(BaseModel):
    fixtures: list[dict[str, Any]]; alert_threshold: int = Field(default=75, ge=50, le=95); min_similar_matches: int = Field(default=20, ge=1, le=500); limit: int = Field(default=10, ge=1, le=100)

@router.get("/health")
def comeback_health(): return {"enabled":True,"markets":["2/1","1/2"],"default_alert_threshold":75,"note":"Scores are ranking signals, not calibrated probabilities."}
@router.post("/evaluate")
def comeback_evaluate(request: ComebackEvaluateRequest): return evaluate_comeback(request.payload, alert_threshold=request.alert_threshold)
@router.post("/scan")
def comeback_scan(request: ComebackScanRequest):
    items=scan_comeback_candidates(request.fixtures,alert_threshold=request.alert_threshold,min_similar_matches=request.min_similar_matches,limit=request.limit)
    return {"count":len(items),"threshold":request.alert_threshold,"items":items}

@router.get("/stored-readiness")
def stored_comeback_readiness(hours:int=Query(default=36,ge=1,le=168)):
    start=datetime.now(timezone.utc); fixtures=load_comeback_fixtures(start=start,end=start+timedelta(hours=hours),limit=1000)
    return {"window_hours":hours,**comeback_data_readiness(fixtures)}

@router.get("/stored-candidates")
def stored_comeback_candidates(hours:int=Query(default=36,ge=1,le=168),alert_threshold:int=Query(default=75,ge=50,le=95),min_similar_matches:int=Query(default=20,ge=1,le=500),limit:int=Query(default=10,ge=1,le=100),use_calibrated_thresholds:bool=Query(default=True)):
    start=datetime.now(timezone.utc); fixtures=load_comeback_fixtures(start=start,end=start+timedelta(hours=hours),limit=2000)
    readiness=comeback_data_readiness(fixtures); backtest=run_comeback_backtest(lookback_days=1460,min_matches=100)
    enough=bool(backtest.get("enough_data")); calibration=calibrate_thresholds(backtest) if use_calibrated_thresholds else None
    t21=int(calibration["2/1"]["threshold"]) if calibration and enough else alert_threshold
    t12=int(calibration["1/2"]["threshold"]) if calibration and enough else alert_threshold
    items=scan_comeback_candidates(fixtures,alert_threshold=alert_threshold,threshold_2_1=t21,threshold_1_2=t12,min_similar_matches=min_similar_matches,limit=limit,ranking_only=not enough)
    return {"window_hours":hours,"mode":"CALIBRATED" if enough else "LIVE_RANKING","thresholds":{"2/1":t21,"1/2":t12},"readiness":readiness,"count":len(items),"items":items}

@router.get("/backtest")
def comeback_backtest(lookback_days:int=Query(default=1460,ge=90,le=3650),min_matches:int=Query(default=100,ge=20,le=5000)):
    result=run_comeback_backtest(lookback_days=lookback_days,min_matches=min_matches); return {**result,"recommended_thresholds":calibrate_thresholds(result)}

def _self_check_payload(hours:int,lookback_days:int,min_matches:int,limit:int)->dict[str,Any]:
    start=datetime.now(timezone.utc); fixtures=load_comeback_fixtures(start=start,end=start+timedelta(hours=hours),limit=2000)
    readiness=comeback_data_readiness(fixtures); backtest=run_comeback_backtest(lookback_days=lookback_days,min_matches=min_matches)
    enough=bool(backtest.get("enough_data")); calibration=calibrate_thresholds(backtest)
    t21=int(calibration["2/1"]["threshold"]) if enough else 75; t12=int(calibration["1/2"]["threshold"]) if enough else 75
    items=scan_comeback_candidates(fixtures,alert_threshold=75,threshold_2_1=t21,threshold_1_2=t12,min_similar_matches=20,limit=limit,ranking_only=not enough)
    return {"ready_for_live_use":readiness.get("ready",0)>0,"calibrated":enough,"mode":"CALIBRATED" if enough else "LIVE_RANKING","backtest":{"eligible_matches":backtest.get("eligible_matches",0),"minimum_required":backtest.get("minimum_required",min_matches)},"thresholds":{"2/1":t21,"1/2":t12},"readiness":readiness,"candidate_count":len(items),"top_candidates":items}

@router.get("/self-check")
def comeback_self_check(hours:int=Query(default=36,ge=1,le=168),lookback_days:int=Query(default=1460,ge=90,le=3650),min_matches:int=Query(default=100,ge=20,le=5000),limit:int=Query(default=3,ge=1,le=20)):
    return _self_check_payload(hours,lookback_days,min_matches,limit)

@router.get("/self-check.txt",response_class=PlainTextResponse)
def comeback_self_check_text(hours:int=Query(default=36,ge=1,le=168),lookback_days:int=Query(default=1460,ge=90,le=3650),min_matches:int=Query(default=100,ge=20,le=5000),limit:int=Query(default=3,ge=1,le=20)):
    p=_self_check_payload(hours,lookback_days,min_matches,limit); b=p["backtest"]; r=p["readiness"]
    lines=["ASLAN 2/1-1/2 MOTOR",f"RUNNING: {'YES' if p['ready_for_live_use'] else 'NO'} | MODE: {p['mode']}",f"BACKTEST: {b['eligible_matches']}/{b['minimum_required']} (calibration continues)",f"FIXTURES: {r.get('fixtures',0)} | DATA READY: {r.get('ready',0)}",f"RANKED: {p['candidate_count']}"]
    for i,item in enumerate(p["top_candidates"],1): lines.append(f"{i}. {item.get('home_team')} - {item.get('away_team')} | {item.get('preferred_market')} | score={item.get('score')} | 2/1={item.get('score_2_1')} | 1/2={item.get('score_1_2')} | quality={item.get('quality_score')}")
    return "\n".join(lines)+"\n"

@router.get("/threshold-guide")
def comeback_threshold_guide(threshold:int=Query(default=75,ge=50,le=95)):
    return {"threshold":threshold,"bands":[{"min":88,"label":"VERY_STRONG"},{"min":82,"label":"STRONG"},{"min":threshold,"label":"WATCH"}]}
