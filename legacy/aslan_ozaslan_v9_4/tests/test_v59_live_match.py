import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'src'))
from aslan_ozaslan.live_v5 import *
from aslan_ozaslan.admin.live_match_page import render_live_match_page
class LiveMatchTests(unittest.TestCase):
    def initial(self): return LiveProbabilityState(0,0.50,0.28,0.22,0,0,0,0)
    def test_store_idempotent(self):
        s=LiveEventStore(); e=LiveMatchEvent('e1',10,'home','SHOT_ON_TARGET',1)
        self.assertTrue(s.append(e)); self.assertFalse(s.append(e)); self.assertEqual(s.count(),1)
    def test_momentum(self):
        events=(LiveMatchEvent('e1',60,'away','SHOT',1),LiveMatchEvent('e2',69,'home','SHOT_ON_TARGET',1),LiveMatchEvent('e3',70,'home','DANGEROUS_ATTACK',1))
        m=MomentumAnalyzer().analyze(events=events,home_team_id='home',away_team_id='away',current_minute=70,window_minutes=15)
        self.assertEqual(m.dominant_team,'HOME'); self.assertGreater(m.net_momentum,0)
    def test_processor(self):
        p=LiveMatchProcessor(home_team_id='home',away_team_id='away',initial_state=self.initial())
        p.process(LiveMatchEvent('e1',25,'home','SHOT_ON_TARGET',1))
        goal=p.process(LiveMatchEvent('e2',30,'home','GOAL',1))
        self.assertEqual(goal.state.home_goals,1); self.assertGreater(goal.state.home_probability,0.50)
        self.assertAlmostEqual(goal.state.home_probability+goal.state.draw_probability+goal.state.away_probability,1.0)
        dup=p.process(LiveMatchEvent('e2',30,'home','GOAL',1)); self.assertFalse(dup.accepted); self.assertEqual(dup.state.home_goals,1)
        page=render_live_match_page(goal.state,goal.momentum,p.store.ordered()); self.assertIn('Canlı Maç Analizi',page); self.assertIn('Olay akışı',page)
if __name__=='__main__': unittest.main()
