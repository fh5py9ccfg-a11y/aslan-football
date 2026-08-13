from __future__ import annotations
from dataclasses import dataclass
import json, math, statistics, time

@dataclass(frozen=True)
class LiveMatchEvent:
    match_id: str
    event_id: str
    event_type: str
    team_id: str | None
    player_id: str | None
    minute: int
    event_time: int
    xg: float
    value: float | None
    source: str

@dataclass(frozen=True)
class MatchAnalyticsSnapshot:
    match_id: str
    last_event_time: int
    event_count: int
    home_team_id: str | None
    away_team_id: str | None
    home_xg: float
    away_xg: float
    home_momentum: float
    away_momentum: float
    possession_trend: float
    anomaly_score: float
    updated_at: int

@dataclass(frozen=True)
class StreamingDecision:
    match_id: str
    trigger: str
    severity: str
    reason: str
    event_time: int

class OutOfOrderEvent(RuntimeError): pass
class DuplicateStreamEvent(RuntimeError): pass

class RedisStreamingRepository:
    def __init__(self, client, *, prefix="aslan:streaming", ttl_seconds=86400):
        self.client, self.prefix, self.ttl_seconds = client, prefix, ttl_seconds

    def mark_event(self, event):
        return bool(self.client.set(
            f"{self.prefix}:dedup:{event.match_id}:{event.event_id}",
            "1", nx=True, ex=self.ttl_seconds
        ))

    def append_event(self, event):
        payload = json.dumps(event.__dict__, ensure_ascii=False, separators=(",", ":"))
        self.client.zadd(f"{self.prefix}:events:{event.match_id}", {payload: float(event.event_time)})

    def list_events(self, match_id, *, limit=500):
        values = self.client.zrange(f"{self.prefix}:events:{match_id}", 0, max(0, limit-1))
        out = []
        for payload in values:
            if isinstance(payload, bytes): payload = payload.decode()
            out.append(LiveMatchEvent(**json.loads(payload)))
        return tuple(out)

    def save_snapshot(self, snapshot):
        self.client.setex(
            f"{self.prefix}:snapshot:{snapshot.match_id}", self.ttl_seconds,
            json.dumps(snapshot.__dict__, ensure_ascii=False, separators=(",", ":"))
        )
        return snapshot

    def get_snapshot(self, match_id):
        payload = self.client.get(f"{self.prefix}:snapshot:{match_id}")
        if payload is None: return None
        if isinstance(payload, bytes): payload = payload.decode()
        return MatchAnalyticsSnapshot(**json.loads(payload))

    def save_decision(self, decision):
        token = f"{decision.match_id}:{decision.trigger}:{decision.event_time}"
        self.client.setex(
            f"{self.prefix}:decision:{token}", self.ttl_seconds,
            json.dumps(decision.__dict__, ensure_ascii=False, separators=(",", ":"))
        )
        self.client.sadd(f"{self.prefix}:decisions:{decision.match_id}", token)
        return decision

    def list_decisions(self, match_id, *, limit=100):
        items = []
        for token in self.client.smembers(f"{self.prefix}:decisions:{match_id}"):
            if isinstance(token, bytes): token = token.decode()
            payload = self.client.get(f"{self.prefix}:decision:{token}")
            if payload is None: continue
            if isinstance(payload, bytes): payload = payload.decode()
            items.append(StreamingDecision(**json.loads(payload)))
        items.sort(key=lambda x: x.event_time, reverse=True)
        return tuple(items[:limit])

class MomentumEngine:
    WEIGHTS = {
        "GOAL": 5.0, "SHOT_ON_TARGET": 2.0, "SHOT": 1.0,
        "CORNER": 0.5, "RED_CARD": -3.0,
        "YELLOW_CARD": -0.5, "POSSESSION": 0.2,
    }

    @classmethod
    def calculate(cls, events, *, team_id, current_minute, window_minutes=10):
        score = 0.0
        for event in events:
            if event.team_id != team_id: continue
            age = current_minute - event.minute
            if age < 0 or age > window_minutes: continue
            recency = max(0.0, 1.0 - age / max(1, window_minutes))
            score += cls.WEIGHTS.get(event.event_type, 0.0) * recency
            score += max(0.0, event.xg) * 2.0 * recency
        return round(score, 6)

class StreamingAnomalyDetector:
    @staticmethod
    def calculate(events):
        if len(events) < 3: return 0.0
        intervals = [b.event_time-a.event_time for a,b in zip(events[:-1], events[1:])]
        mean = statistics.fmean(intervals)
        dev = statistics.pstdev(intervals)
        burst = 0.0 if math.isclose(dev, 0.0) else dev/max(1.0, mean)
        xg = max((e.xg for e in events), default=0.0)
        return round(min(10.0, burst + xg*2.0), 6)

class StreamingAnalyticsEngine:
    def __init__(self, *, repository, allowed_lateness_seconds=10, decision_threshold=4.0):
        self.repository = repository
        self.allowed_lateness_seconds = allowed_lateness_seconds
        self.decision_threshold = decision_threshold

    def process(self, event, *, home_team_id=None, away_team_id=None, now=None):
        if not self.repository.mark_event(event):
            raise DuplicateStreamEvent("Event daha önce işlendi")
        previous = self.repository.get_snapshot(event.match_id)
        if previous and event.event_time < previous.last_event_time-self.allowed_lateness_seconds:
            raise OutOfOrderEvent("Event allowed lateness sınırını aştı")
        self.repository.append_event(event)
        events = self.repository.list_events(event.match_id)
        home = home_team_id or (previous.home_team_id if previous else None)
        away = away_team_id or (previous.away_team_id if previous else None)
        minute = max(e.minute for e in events)
        hxg = round(sum(e.xg for e in events if e.team_id == home), 6)
        axg = round(sum(e.xg for e in events if e.team_id == away), 6)
        hm = MomentumEngine.calculate(events, team_id=home, current_minute=minute) if home else 0.0
        am = MomentumEngine.calculate(events, team_id=away, current_minute=minute) if away else 0.0
        possession = [float(e.value) for e in events if e.event_type=="POSSESSION" and e.value is not None]
        trend = round(possession[-1]-possession[0], 6) if len(possession)>=2 else 0.0
        anomaly = StreamingAnomalyDetector.calculate(events)
        snapshot = MatchAnalyticsSnapshot(
            match_id=event.match_id, last_event_time=max(e.event_time for e in events),
            event_count=len(events), home_team_id=home, away_team_id=away,
            home_xg=hxg, away_xg=axg, home_momentum=hm, away_momentum=am,
            possession_trend=trend, anomaly_score=anomaly,
            updated_at=int(now if now is not None else time.time())
        )
        self.repository.save_snapshot(snapshot)
        decisions = []
        gap = abs(hm-am)
        if gap >= self.decision_threshold:
            decisions.append(self.repository.save_decision(StreamingDecision(
                match_id=event.match_id, trigger="MOMENTUM_SHIFT",
                severity="HIGH" if gap>=7 else "MEDIUM",
                reason="Momentum farkı inference tetikleme eşiğini aştı",
                event_time=event.event_time
            )))
        if anomaly >= 3.0:
            decisions.append(self.repository.save_decision(StreamingDecision(
                match_id=event.match_id, trigger="STREAM_ANOMALY",
                severity="HIGH" if anomaly>=5 else "MEDIUM",
                reason="Canlı olay akışında anomali tespit edildi",
                event_time=event.event_time
            )))
        return snapshot, tuple(decisions)
