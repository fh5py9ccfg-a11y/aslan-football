import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.scout_v8 import (
    PlayerDNA,
    ScoutCandidate,
    PlayerDNAAnalyzer,
    PlayerDevelopmentProjector,
    LeagueTranslationModel,
    HiddenGemDetector,
    ScoutIntelligenceService,
    ScoutNarrativeBuilder,
)
from aslan_ozaslan.admin.scout_intelligence_page import (
    render_scout_intelligence_page,
)

class ScoutIntelligenceTests(unittest.TestCase):
    def dna(self, player_id, offset=0.0):
        return PlayerDNA(
            player_id=player_id,
            passing=0.78 + offset,
            progression=0.76 + offset,
            dribbling=0.70 + offset,
            pressing=0.72 + offset,
            defending=0.66 + offset,
            aerial=0.52 + offset,
            finishing=0.61 + offset,
            creativity=0.75 + offset,
            athleticism=0.74 + offset,
            consistency=0.80 + offset,
        )

    def candidate(self):
        return ScoutCandidate(
            player_id="p1",
            age=21,
            current_level=0.68,
            potential_level=0.88,
            market_value=4_000_000,
            annual_salary=700_000,
            injury_risk=0.18,
            adaptation_risk=0.22,
            discipline_risk=0.10,
            source_league_strength=0.58,
            target_league_strength=0.78,
        )

    def test_dna_similarity(self):
        target = self.dna("p1")
        candidates = [
            self.dna("p2", -0.01),
            self.dna("p3", -0.25),
        ]
        results = PlayerDNAAnalyzer().similarity(
            target,
            candidates,
            limit=2,
        )
        self.assertEqual(results[0].player_id, "p2")
        self.assertGreater(
            results[0].similarity,
            results[1].similarity,
        )

    def test_development_translation_and_hidden_gem(self):
        projection = PlayerDevelopmentProjector().project(
            age=21,
            current_level=0.68,
            potential_level=0.88,
            consistency=0.80,
            minutes_share=0.75,
        )
        self.assertGreater(projection.level_24m, 0.68)

        translation = LeagueTranslationModel().evaluate(
            player_level=projection.level_12m,
            source_strength=0.58,
            target_strength=0.78,
            adaptation_risk=0.22,
        )
        self.assertGreater(translation.score, 0.50)

        hidden = HiddenGemDetector().score(
            current_level=0.68,
            potential_level=0.88,
            market_value=4_000_000,
            annual_salary=700_000,
            age=21,
            risk_score=0.20,
        )
        self.assertGreater(hidden, 0.40)

    def test_full_scout_assessment_and_page(self):
        service = ScoutIntelligenceService()
        assessment = service.assess(
            candidate=self.candidate(),
            player_dna=self.dna("p1"),
            desired_dna=self.dna("desired", -0.02),
            consistency=0.80,
            minutes_share=0.75,
        )
        self.assertGreater(assessment.club_fit_score, 0.85)
        self.assertIn(
            assessment.recommendation,
            {"PRIORITY_TARGET", "SCOUT_DEEPLY"},
        )

        narrative = ScoutNarrativeBuilder().build(assessment)
        self.assertIn("Kulüp uyumu", narrative)

        page = render_scout_intelligence_page(
            assessment,
            narrative,
        )
        self.assertIn("Scout Intelligence", page)
        self.assertIn("Gizli yetenek", page)
        self.assertIn("Lig geçişi", page)

if __name__ == "__main__":
    unittest.main()
