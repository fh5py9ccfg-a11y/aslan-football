from dataclasses import dataclass
@dataclass(frozen=True)
class MomentumSnapshot:
    home_momentum: float
    away_momentum: float
    net_momentum: float
    dominant_team: str

class MomentumAnalyzer:
    WEIGHTS={'GOAL':5.0,'SHOT':0.8,'SHOT_ON_TARGET':1.5,'RED_CARD':-4.0,'YELLOW_CARD':-0.3,'DANGEROUS_ATTACK':0.6,'SUBSTITUTION':0.1}
    def analyze(self, *, events, home_team_id, away_team_id, current_minute, window_minutes=15):
        if window_minutes <= 0: raise ValueError('window_minutes pozitif olmalıdır')
        home=away=0.0
        lower=max(0,current_minute-window_minutes)
        for e in events:
            if not lower <= e.minute <= current_minute: continue
            weight=self.WEIGHTS[e.event_type]*e.value
            recency=1.0-((current_minute-e.minute)/window_minutes)*0.4
            score=weight*max(recency,0.6)
            if e.team_id==home_team_id: home+=score
            elif e.team_id==away_team_id: away+=score
        net=home-away
        dominant='HOME' if net>0.75 else 'AWAY' if net<-0.75 else 'BALANCED'
        return MomentumSnapshot(home,away,net,dominant)
