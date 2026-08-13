import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslan_ozaslan.squad_v5 import *
from aslan_ozaslan.admin.lineup_page import render_lineup_page

class SquadEngineTests(unittest.TestCase):
    def test_fatigue_and_chemistry(self):
        assessment = FatigueModel().assess(FatigueInput(900,5,2,8))
        self.assertGreater(assessment.fatigue_score,.5)
        report = SquadChemistryAnalyzer().analyze(
            ["p1","p2","p3"],
            [ChemistryLink("p1","p2",.9), ChemistryLink("p1","p3",.7)]
        )
        self.assertEqual(report.linked_pairs,2)
        self.assertEqual(report.missing_pairs,1)

    def test_lineup_and_rotation(self):
        players = [
            SquadPlayer("gk1","GK","keeper",8,.2,True),
            SquadPlayer("gk2","GK","keeper",7.5,.1,True),
            SquadPlayer("df1","DF","stopper",8.5,.3,True),
            SquadPlayer("df2","DF","cover",8.2,.2,True),
            SquadPlayer("df3","DF","stopper",7.8,.8,True),
            SquadPlayer("mf1","MF","creator",9,.4,True),
            SquadPlayer("mf2","MF","runner",8.7,.2,True),
            SquadPlayer("fw1","FW","striker",9.4,.3,True),
            SquadPlayer("fw2","FW","striker",8,.1,True),
        ]
        requirements = [
            FormationRequirement("GK",1), FormationRequirement("DF",2),
            FormationRequirement("MF",2), FormationRequirement("FW",1),
        ]
        links = [
            ChemistryLink("df1","df2",.9),
            ChemistryLink("mf1","mf2",.85),
            ChemistryLink("mf1","fw1",.8),
        ]
        selection = LineupOptimizer().optimize(
            players=players, requirements=requirements, chemistry_links=links
        )
        self.assertEqual(len(selection.player_ids),6)
        self.assertNotIn("df3", selection.player_ids)
        recommendation = RotationAdvisor().recommend(players, fatigue_threshold=.7)
        self.assertIn("df3", recommendation.rest_player_ids)
        page = render_lineup_page(selection, recommendation)
        self.assertIn("Kadro ve İlk 11 Analizi", page)

if __name__ == "__main__":
    unittest.main()
