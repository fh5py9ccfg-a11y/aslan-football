import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from aslan_ozaslan.tactics_v5 import *
from aslan_ozaslan.squad_v5 import LineupSelection
from aslan_ozaslan.admin.tactical_page import render_tactical_page
class TacticalEngineTests(unittest.TestCase):
    def p(self,id,a,b,c,d,e,f,g,h): return TacticalProfile(id,a,b,c,d,e,f,g,h)
    def test_formation(self):
        self.assertTrue(FormationValidator().validate(Formation('4-3-3',4,3,3)).valid)
        self.assertIn('formation_shape_mismatch',FormationValidator().validate(Formation('4-3-3',3,4,3)).issues)
    def test_matchup_scenario_compatibility(self):
        home=self.p('home',.75,.70,.68,.72,.62,.78,.55,.66); away=self.p('away',.58,.82,.52,.60,.54,.63,.70,.48)
        report=TacticalMatchupAnalyzer().analyze(home,away)
        self.assertEqual(report.advantage,'HOME'); self.assertGreater(report.transition_edge,0)
        adjustment=TacticalScenarioEngine().adjust(home,MatchScenario(80,-1,0,False))
        self.assertEqual(adjustment.risk_level,'HIGH'); self.assertGreater(adjustment.tempo,home.tempo)
        lineup=LineupSelection(('p1','p2','p3'),82,.84,.22,70)
        compat=TacticalCompatibilityEvaluator().evaluate(lineup,home)
        self.assertGreater(compat.compatibility_score,.7)
        page=render_tactical_page(report,adjustment,compat)
        self.assertIn('Taktik Eşleşme Analizi',page); self.assertIn('Kadro-taktik uyumu',page)
if __name__=='__main__': unittest.main()
