import sys, unittest, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aslan_ozaslan.operating_system_v9 import (
    ExpertDecision,
    KnowledgeRelation,
    ExpertRegistry,
    FootballDecisionOrchestrator,
    FootballKnowledgeGraph,
    DecisionOutcome,
    ContinuousLearningEvaluator,
    DecisionAuditRepository,
    FootballOperatingSystem,
)
from aslan_ozaslan.admin.football_operating_system_page import (
    render_football_operating_system_page,
)

class StaticExpert:
    def __init__(self, decision):
        self.decision = decision

    def evaluate(self, context):
        return self.decision

class FootballOperatingSystemTests(unittest.TestCase):
    def decisions(self):
        return (
            ExpertDecision(
                "scout","SIGN",0.82,0.28,
                "Oyuncu rol ve potansiyel açısından uygun.",
                "SCOUT",
            ),
            ExpertDecision(
                "finance","SIGN",0.74,0.35,
                "Maliyet mevcut bütçe sınırları içinde.",
                "FINANCE",
            ),
            ExpertDecision(
                "risk","REVIEW",0.68,0.48,
                "Adaptasyon riski için ek inceleme gerekli.",
                "RISK",
            ),
        )

    def test_registry_orchestration_and_audit(self):
        registry = ExpertRegistry()
        for item in self.decisions():
            registry.register(
                item.expert,
                StaticExpert(item),
            )

        orchestrator = FootballDecisionOrchestrator(
            expert_weights={
                "scout": 1.2,
                "finance": 1.0,
                "risk": 0.8,
            },
            minimum_consensus=0.55,
        )

        with tempfile.TemporaryDirectory() as temp:
            audit = DecisionAuditRepository(
                Path(temp) / "audit.json"
            )
            platform = FootballOperatingSystem(
                registry=registry,
                orchestrator=orchestrator,
                audit_repository=audit,
            )
            decision, experts = platform.decide(
                subject_id="player-p1",
                context={"player_id": "p1"},
            )

            self.assertEqual(
                decision.final_recommendation,
                "SIGN",
            )
            self.assertTrue(decision.approved)
            self.assertIn("risk", decision.dissenting_experts)
            self.assertEqual(
                len(audit.list_for_subject("player-p1")),
                1,
            )

            page = render_football_operating_system_page(
                decision,
                experts,
            )
            self.assertIn("Football Operating System", page)
            self.assertIn("Uzman kararları", page)

    def test_knowledge_graph_paths_and_persistence(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "graph.json"
            graph = FootballKnowledgeGraph(path)
            graph.add(KnowledgeRelation(
                "player-p1","PLAYS_ROLE","role-8",0.90,{}
            ))
            graph.add(KnowledgeRelation(
                "role-8","SUITS_STYLE","high-press",0.85,{}
            ))
            graph.add(KnowledgeRelation(
                "high-press","USED_BY","coach-c1",0.80,{}
            ))

            paths = graph.infer_paths(
                "player-p1",
                "coach-c1",
                max_depth=3,
            )
            self.assertEqual(len(paths), 1)
            self.assertGreater(graph.path_strength(paths[0]), 0.60)

            reloaded = FootballKnowledgeGraph(path)
            self.assertEqual(
                len(reloaded.neighbors("player-p1")),
                1,
            )

    def test_continuous_learning_weights(self):
        outcomes = (
            DecisionOutcome("d1","scout",0.80,1.00),
            DecisionOutcome("d2","scout",0.70,0.80),
            DecisionOutcome("d3","finance",0.85,0.30),
        )
        reports = ContinuousLearningEvaluator().evaluate(
            outcomes
        )
        by_expert = {item.expert: item for item in reports}
        self.assertGreater(
            by_expert["scout"].suggested_weight,
            by_expert["finance"].suggested_weight,
        )

if __name__ == "__main__":
    unittest.main()
