from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo
from fastapi import APIRouter, Query
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field
from .comeback_backtest import run_comeback_backtest
from .comeback_calibration import calibrate_thresholds
from .comeback_detector import evaluate_comeback
from .comeback_fixture_adapter import comeback_data_readiness, load_comeback_fixtures
from .comeback_scanner import scan_comeback_candidates

router=APIRouter(prefix="/api/comeback",tags=["HT/FT Comeback Detector"])
TR=ZoneInfo("Europe/Istanbul")
class ComebackEvaluateRequest(BaseModel): payload:dict[str,Any]; alert_threshold:int=Field(default=75,ge=50,le=95)
class ComebackScanRequest(BaseModel): fixtures:list[dict[str,Any]]; alert_threshold:int=Field(default=75,ge=50,le=95); min_similar_matches:int=Field(default=20,ge=1,le=500); limit:int=Field(default=10,ge=1,le=100)

def _today_window():
    now=datetime.now(TR); start_local=now.replace(hour=0,minute=0,second=0,microsecond=0); end_local=start_local+timedelta(days=1)
    return start_local.astimezone(timezone.utc),end_local.astimezone(timezone.utc),start_local.date().isoformat()

def _today_fixtures(limit=2000):
    start,end,_=_today_window(); return load_comeback_fixtures(start=start,end=end,limit=limit)

@router.get("/health")
def comeback_health(): return {"enabled":True,"markets":["2/1","1/2"],"day_timezone":"Europe/Istanbul"}
@router.post("/evaluate")
def comeback_evaluate(request:ComebackEvaluateRequest): return evaluate_comeback(request.payload,alert_threshold=request.alert_threshold)
@router.post("/scan")
def comeback_scan(request:ComebackScanRequest):
    items=scan_comeback_candidates(request.fixtures,alert_threshold=request.alert_threshold,min_similar_matches=request.min_similar_matches,limit=request.limit); return {"count":len(items),"items":items}
@router.get("/stored-readiness")
def stored_comeback_readiness():
    fixtures=_today_fixtures(1000); _,_,day=_today_window(); return {"date_tr":day,**comeback_data_readiness(fixtures)}
@router.get("/stored-candidates")
def stored_comeback_candidates(alert_threshold:int=Query(default=75,ge=50,le=95),limit:int=Query(default=10,ge=1,le=100)):
    fixtures=_today_fixtures(); readiness=comeback_data_readiness(fixtures); backtest=run_comeback_backtest(lookback_days=1460,min_matches=100); enough=bool(backtest.get("enough_data")); calibration=calibrate_thresholds(backtest)
    t21=int(calibration["2/1"]["threshold"]) if enough else alert_threshold; t12=int(calibration["1/2"]["threshold"]) if enough else alert_threshold
    items=scan_comeback_candidates(fixtures,alert_threshold=alert_threshold,threshold_2_1=t21,threshold_1_2=t12,min_similar_matches=20,limit=limit,ranking_only=not enough); _,_,day=_today_window()
    return {"date_tr":day,"mode":"CALIBRATED" if enough else "LIVE_RANKING","readiness":readiness,"count":len(items),"items":items}
@router.get("/backtest")
def comeback_backtest(lookback_days:int=Query(default=1460,ge=90,le=3650),min_matches:int=Query(default=100,ge=20,le=5000)):
    result=run_comeback_backtest(lookback_days=lookback_days,min_matches=min_matches); return {**result,"recommended_thresholds":calibrate_thresholds(result)}

def _self_check_payload(min_matches:int,limit:int):
    fixtures=_today_fixtures(); readiness=comeback_data_readiness(fixtures); backtest=run_comeback_backtest(lookback_days=1460,min_matches=min_matches); enough=bool(backtest.get("enough_data")); calibration=calibrate_thresholds(backtest)
    t21=int(calibration["2/1"]["threshold"]) if enough else 75; t12=int(calibration["1/2"]["threshold"]) if enough else 75
    items=scan_comeback_candidates(fixtures,alert_threshold=75,threshold_2_1=t21,threshold_1_2=t12,min_similar_matches=20,limit=limit,ranking_only=not enough); _,_,day=_today_window()
    return {"date_tr":day,"running":readiness.get("ready",0)>0,"mode":"CALIBRATED" if enough else "LIVE_RANKING","backtest":backtest,"readiness":readiness,"items":items}
@router.get("/self-check")
def comeback_self_check(min_matches:int=Query(default=100,ge=20,le=5000),limit:int=Query(default=3,ge=1,le=20)): return _self_check_payload(min_matches,limit)
@router.get("/self-check.txt",response_class=PlainTextResponse)
def comeback_self_check_text(min_matches:int=Query(default=100,ge=20,le=5000),limit:int=Query(default=3,ge=1,le=20)):
    p=_self_check_payload(min_matches,limit); b=p["backtest"]; r=p["readiness"]; items=p["items"]
    lines=["ASLAN 2/1-1/2 MOTOR",f"DATE(TR): {p['date_tr']} | TODAY ONLY: YES",f"RUNNING: {'YES' if p['running'] else 'NO'} | MODE: {p['mode']}",f"BACKTEST: {b.get('eligible_matches',0)}/{b.get('minimum_required',min_matches)}",f"TODAY FIXTURES: {r.get('fixtures',0)} | DATA READY: {r.get('ready',0)}",f"RANKED: {len(items)}"]
    for i,item in enumerate(items,1): lines.append(f"{i}. {item.get('home_team')} - {item.get('away_team')} | {item.get('preferred_market')} | score={item.get('score')} | 2/1={item.get('score_2_1')} | 1/2={item.get('score_1_2')} | quality={item.get('quality_score')}")
    return "\n".join(lines)+"\n"
@router.get("/threshold-guide")
def comeback_threshold_guide(threshold:int=Query(default=75,ge=50,le=95)): return {"threshold":threshold}
