import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.adapters_v9 import (
    FootballDecisionContext,
    TransferIntelligenceAdapter,
    ScoutIntelligenceAdapter,
    FootballOperatingSystemBuilder,
)
from aslan_ozaslan.transfer_v8 import (
    TransferPlayerProfile,
    TransferIntelligenceService,
)
from aslan_ozaslan.scout_v8 import (
    PlayerDNA,
    ScoutCandidate,
    ScoutIntelligenceService,
)
from aslan_ozaslan.operating_system_v9 import DecisionAuditRepository
from aslan_ozaslan.admin.adapter_status_page import (
    render_adapter_status_page,
)

class ExpertAdapterTests(unittest.TestCase):
    def transfer_profile(self):
        return TransferPlayerProfile(
            player_id="p1",
            name="Oyuncu",
            position="MF",
            age=23,
            current_value_score=8.4,
            form_trend=0.8,
            injury_days_last_365=12,
            minutes_last_365=2900,
            annual_salary=1_800_000,
            estimated_fee=10_000_000,
            contract_months_remaining=18,
            league_strength=0.80,
        )

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

    def scout_candidate(self):
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

    def test_transfer_and_scout_adapters(self):
        context = FootballDecisionContext(
            subject_id="player-p1",
            decision_type="TRANSFER",
            payload={
                "profile": self.transfer_profile(),
                "candidate": self.scout_candidate(),
                "player_dna": self.dna("p1"),
                "desired_dna": self.dna("desired", -0.02),
                "consistency": 0.80,
                "minutes_share": 0.75,
            },
            reliability_score=0.90,
        )

        transfer = TransferIntelligenceAdapter(
            TransferIntelligenceService()
        ).evaluate(context)
        scout = ScoutIntelligenceAdapter(
            ScoutIntelligenceService()
        ).evaluate(context)

        self.assertIn(
            transfer.recommendation,
            {"SIGN", "SIGN_WITH_REVIEW", "MONITOR", "REJECT"},
        )
        self.assertIn(
            scout.recommendation,
            {"SIGN", "SIGN_WITH_REVIEW", "MONITOR", "REJECT"},
        )

    def test_builder_operating_system_and_status_page(self):
        transfer_adapter = TransferIntelligenceAdapter(
            TransferIntelligenceService()
        )
        scout_adapter = ScoutIntelligenceAdapter(
            ScoutIntelligenceService()
        )

        with tempfile.TemporaryDirectory() as temp:
            audit = DecisionAuditRepository(
                Path(temp) / "audit.json"
            )
            builder = (
                FootballOperatingSystemBuilder()
                .add_adapter(transfer_adapter, weight=1.0)
                .add_adapter(scout_adapter, weight=1.2)
                .with_policy(
                    minimum_consensus=0.45,
                    maximum_risk=0.75,
                )
            )
            platform = builder.build(
                audit_repository=audit
            )

            context = FootballDecisionContext(
                subject_id="player-p1",
                decision_type="TRANSFER",
                payload={
                    "profile": self.transfer_profile(),
                    "candidate": self.scout_candidate(),
                    "player_dna": self.dna("p1"),
                    "desired_dna": self.dna("desired", -0.02),
                    "consistency": 0.80,
                    "minutes_share": 0.75,
                },
                reliability_score=0.90,
            )
            decision, experts = platform.decide(
                subject_id=context.subject_id,
                context=context,
            )
            self.assertTrue(decision.final_recommendation)
            self.assertEqual(len(experts), 2)
            self.assertEqual(
                len(audit.list_for_subject("player-p1")),
                1,
            )

            page = render_adapter_status_page(
                builder.registry,
                builder.weights,
            )
            self.assertIn("Football OS Expert Adapters", page)
            self.assertIn("transfer_intelligence", page)
            self.assertIn("scout_intelligence", page)

if __name__ == "__main__":
    unittest.main()
