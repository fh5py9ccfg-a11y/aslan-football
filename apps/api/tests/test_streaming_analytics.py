import pytest
from apps.api.app.streaming_analytics import (
    DuplicateStreamEvent, LiveMatchEvent, OutOfOrderEvent,
    RedisStreamingRepository, StreamingAnalyticsEngine,
)

class Redis:
    def __init__(self):
        self.values, self.sets, self.sorted_sets = {}, {}, {}
    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.values: return False
        self.values[key] = value; return True
    def setex(self, key, ttl, value): self.values[key] = value
    def get(self, key): return self.values.get(key)
    def sadd(self, key, value): self.sets.setdefault(key, set()).add(value)
    def smembers(self, key): return self.sets.get(key, set())
    def zadd(self, key, mapping):
        b = self.sorted_sets.setdefault(key, [])
        for value, score in mapping.items(): b.append((float(score), value))
        b.sort(key=lambda x: x[0])
    def zrange(self, key, start, stop):
        b = self.sorted_sets.get(key, [])
        return [v for _,v in b[start:stop+1]]

def build():
    return StreamingAnalyticsEngine(
        repository=RedisStreamingRepository(Redis(), prefix="stream"),
        allowed_lateness_seconds=5, decision_threshold=2.0,
    )

def event(eid, typ, team, minute, ts, xg=0.0, value=None):
    return LiveMatchEvent("m1", eid, typ, team, None, minute, ts, xg, value, "provider")

def test_snapshot_momentum_and_xg():
    e = build()
    e.process(event("e1","SHOT_ON_TARGET","home",10,100,0.3), home_team_id="home", away_team_id="away")
    snap, decisions = e.process(event("e2","GOAL","home",12,110,0.7))
    assert snap.event_count == 2
    assert snap.home_xg == 1.0
    assert snap.home_momentum > snap.away_momentum
    assert decisions

def test_duplicate_rejected():
    e = build(); item = event("e1","SHOT","home",10,100,0.1)
    e.process(item, home_team_id="home", away_team_id="away")
    with pytest.raises(DuplicateStreamEvent): e.process(item)

def test_late_event_rejected():
    e = build()
    e.process(event("e1","SHOT","home",10,100,0.1), home_team_id="home", away_team_id="away")
    e.process(event("e2","SHOT","home",11,110,0.1))
    with pytest.raises(OutOfOrderEvent): e.process(event("e3","SHOT","home",9,90,0.1))

def test_possession_trend():
    e = build()
    e.process(event("e1","POSSESSION","home",10,100,value=48), home_team_id="home", away_team_id="away")
    snap,_ = e.process(event("e2","POSSESSION","home",20,110,value=57))
    assert snap.possession_trend == 9.0
