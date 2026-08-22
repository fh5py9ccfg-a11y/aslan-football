from __future__ import annotations

import json
import math
from collections import defaultdict
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta, timezone
from typing import Any, Iterable, Mapping

from sqlalchemy import select

from .db import SessionLocal
from .models import FixtureModel, MatchEventModel

MARKET_KEYS = (
    "home_win_probability", "draw_probability", "away_win_probability",
    "first_half_home_probability", "first_half_draw_probability", "first_half_away_probability",
)
FINISHED_STATUSES = {"finished", "ft", "after extra time", "after penalties", "aet", "pen"}

@dataclass(frozen=True)
class HistoricalMarketRow:
    fixture_id: str
    vector: tuple[float, ...]
    ht_result: str
    ft_result: str

@dataclass(frozen=True)
class SimilarMarketEvidence:
    matches: int
    two_one_matches: int
    one_two_matches: int
    two_one_rate: float
    one_two_rate: float
    mean_distance: float | None
    def as_dict(self) -> dict:
        return asdict(self)

def _parse_raw(raw_json: str | None) -> dict[str, Any]:
    if not raw_json: return {}
    try: value = json.loads(raw_json)
    except (TypeError, ValueError): return {}
    return value if isinstance(value, dict) else {}

def _feature_source(raw: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("comeback_inputs", "prediction_features", "market_features"):
        value = raw.get(key)
        if isinstance(value, Mapping): return value
    meta = raw.get("meta")
    if isinstance(meta, Mapping) and isinstance(meta.get("comeback_inputs"), Mapping):
        return meta["comeback_inputs"]
    return {}

def _vector(source: Mapping[str, Any]) -> tuple[float, ...] | None:
    values = []
    for key in MARKET_KEYS:
        try: value = float(source[key])
        except (KeyError, TypeError, ValueError): return None
        if value > 1.0: value /= 100.0
        if not 0.0 <= value <= 1.0: return None
        values.append(value)
    return tuple(values)

def _distance(left: tuple[float, ...], right: tuple[float, ...]) -> float:
    weights = (1.25, 0.9, 1.25, 1.0, 0.8, 1.0)
    return math.sqrt(sum(w * (a-b)**2 for a,b,w in zip(left,right,weights)) / sum(weights))

def _outcome_from_events(events: Iterable[MatchEventModel]) -> tuple[str, str]:
    hh=ah=hf=af=0
    for event in events:
        side = str(event.team or "").upper(); minute = int(event.minute or 0)
        if side == "HOME":
            hf += 1; hh += int(minute <= 45)
        elif side == "AWAY":
            af += 1; ah += int(minute <= 45)
    def result(h,a): return "HOME" if h>a else "AWAY" if a>h else "DRAW"
    return result(hh,ah), result(hf,af)

def load_historical_market_pool(*, lookback_days: int = 1460) -> list[HistoricalMarketRow]:
    now = datetime.now(timezone.utc); cutoff = now - timedelta(days=max(90, int(lookback_days)))
    with SessionLocal() as session:
        fixtures = session.execute(select(FixtureModel).where(FixtureModel.kickoff_at >= cutoff, FixtureModel.kickoff_at < now)).scalars().all()
        selected = []
        for fixture in fixtures:
            if str(fixture.status or "").strip().lower() not in FINISHED_STATUSES: continue
            vec = _vector(_feature_source(_parse_raw(fixture.raw_json)))
            if vec is not None: selected.append((fixture, vec))
        ids = [f.fixture_id for f,_ in selected]
        events = session.execute(select(MatchEventModel).where(MatchEventModel.fixture_id.in_(ids), MatchEventModel.event_type == "GOAL")).scalars().all() if ids else []
    grouped = defaultdict(list)
    for event in events: grouped[event.fixture_id].append(event)
    return [HistoricalMarketRow(f.fixture_id, vec, *_outcome_from_events(grouped.get(f.fixture_id, ()))) for f,vec in selected]

def evidence_from_pool(target_inputs: Mapping[str, Any], pool: Iterable[HistoricalMarketRow], *, neighbors: int=80, max_distance: float=0.22, exclude_fixture_id: str|None=None) -> SimilarMarketEvidence:
    target = _vector(target_inputs)
    if target is None: return SimilarMarketEvidence(0,0,0,0.0,0.0,None)
    ranked = []
    for row in pool:
        if exclude_fixture_id and row.fixture_id == exclude_fixture_id: continue
        d = _distance(target, row.vector)
        if d <= max_distance: ranked.append((d,row))
    ranked.sort(key=lambda x:x[0]); chosen = ranked[:max(1,int(neighbors))]
    count=len(chosen); two_one=sum(1 for _,r in chosen if r.ht_result=="AWAY" and r.ft_result=="HOME"); one_two=sum(1 for _,r in chosen if r.ht_result=="HOME" and r.ft_result=="AWAY")
    mean = sum(d for d,_ in chosen)/count if count else None
    return SimilarMarketEvidence(count,two_one,one_two,two_one/count if count else 0.0,one_two/count if count else 0.0,round(mean,6) if mean is not None else None)

def similar_market_evidence(target_inputs: Mapping[str, Any], *, lookback_days:int=1460, neighbors:int=80, max_distance:float=0.22, exclude_fixture_id:str|None=None) -> SimilarMarketEvidence:
    return evidence_from_pool(target_inputs, load_historical_market_pool(lookback_days=lookback_days), neighbors=neighbors, max_distance=max_distance, exclude_fixture_id=exclude_fixture_id)

def enrich_fixtures_with_neighbors(fixtures:list[dict], *, neighbors:int=80, max_distance:float=0.22, lookback_days:int=1460) -> list[dict]:
    pool = load_historical_market_pool(lookback_days=lookback_days)
    enriched=[]
    for fixture in fixtures:
        item=dict(fixture); inputs=dict(item.get("comeback_inputs") or {})
        evidence=evidence_from_pool(inputs,pool,neighbors=neighbors,max_distance=max_distance,exclude_fixture_id=str(item.get("fixture_id") or "") or None)
        if evidence.matches:
            inputs["similar_matches"]=evidence.matches; inputs["similar_2_1_rate"]=evidence.two_one_rate; inputs["similar_1_2_rate"]=evidence.one_two_rate; item["similar_market_evidence"]=evidence.as_dict()
        item["comeback_inputs"]=inputs; item["neighbors_ready"]=evidence.matches>0; enriched.append(item)
    return enriched
