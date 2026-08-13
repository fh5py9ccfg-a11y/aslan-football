from dataclasses import dataclass
from .event_store import LiveEventStore
from .momentum import MomentumAnalyzer
from .probability_update import LiveProbabilityUpdater
@dataclass(frozen=True)
class LiveProcessingResult:
    accepted: bool
    state: object
    momentum: object
class LiveMatchProcessor:
    def __init__(self, *, home_team_id, away_team_id, initial_state):
        self.home_team_id=home_team_id; self.away_team_id=away_team_id; self.state=initial_state
        self.store=LiveEventStore(); self.momentum_analyzer=MomentumAnalyzer(); self.updater=LiveProbabilityUpdater()
    def process(self,event):
        accepted=self.store.append(event)
        if not accepted:
            m=self.momentum_analyzer.analyze(events=self.store.ordered(),home_team_id=self.home_team_id,away_team_id=self.away_team_id,current_minute=self.state.minute)
            return LiveProcessingResult(False,self.state,m)
        hg,ag=self.state.home_goals,self.state.away_goals
        hr,ar=self.state.home_red_cards,self.state.away_red_cards
        if event.event_type=='GOAL':
            if event.team_id==self.home_team_id: hg+=1
            elif event.team_id==self.away_team_id: ag+=1
        elif event.event_type=='RED_CARD':
            if event.team_id==self.home_team_id: hr+=1
            elif event.team_id==self.away_team_id: ar+=1
        m=self.momentum_analyzer.analyze(events=self.store.ordered(),home_team_id=self.home_team_id,away_team_id=self.away_team_id,current_minute=event.minute)
        self.state=self.updater.update(previous=self.state,current_minute=event.minute,home_goals=hg,away_goals=ag,home_red_cards=hr,away_red_cards=ar,momentum=m)
        return LiveProcessingResult(True,self.state,m)
