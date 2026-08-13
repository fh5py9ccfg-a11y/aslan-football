from __future__ import annotations

from .domain import ExecutiveDecisionReport
from .objectives import SeasonObjectiveTracker
from .financials import ExecutiveFinancialAnalyzer
from .risk import StrategicRiskEvaluator

class ExecutiveIntelligenceService:
    def __init__(
        self,
        *,
        objective_tracker=None,
        financial_analyzer=None,
        risk_evaluator=None,
    ):
        self.objective_tracker = (
            objective_tracker or SeasonObjectiveTracker()
        )
        self.financial_analyzer = (
            financial_analyzer or ExecutiveFinancialAnalyzer()
        )
        self.risk_evaluator = (
            risk_evaluator or StrategicRiskEvaluator()
        )

    def evaluate(
        self,
        *,
        snapshot,
        objectives,
        cash_reserve: float,
        annual_commitments: float,
        contract_risk: float,
        sporting_volatility: float,
    ) -> ExecutiveDecisionReport:
        snapshot.validate()

        objective_reports = self.objective_tracker.evaluate(objectives)
        objective_progress = self.objective_tracker.aggregate(
            objective_reports,
            objectives,
        )

        financial = self.financial_analyzer.evaluate(
            revenue=snapshot.revenue,
            wage_cost=snapshot.wage_cost,
            transfer_balance=snapshot.transfer_balance,
            cash_reserve=cash_reserve,
            annual_commitments=annual_commitments,
        )

        strategic_risk = self.risk_evaluator.evaluate(
            squad_age=snapshot.average_squad_age,
            contract_risk=contract_risk,
            wage_ratio=financial.wage_to_revenue_ratio,
            academy_score=snapshot.academy_score,
            sporting_volatility=sporting_volatility,
        )

        health_score = (
            snapshot.sporting_score * 0.22
            + financial.stability_score * 0.22
            + snapshot.squad_score * 0.17
            + snapshot.academy_score * 0.11
            + snapshot.transfer_score * 0.10
            + objective_progress * 0.10
            + (1.0 - strategic_risk.score) * 0.08
        )

        actions = []
        if objective_progress < 0.70:
            actions.append("Sezon hedeflerinde düzeltici plan başlat")
        if financial.status == "AT_RISK":
            actions.append("Maaş ve nakit akışı yeniden yapılandırılsın")
        elif financial.status == "WATCH":
            actions.append("Yeni transferler için mali kontrol uygulansın")
        if strategic_risk.level == "CRITICAL":
            actions.append("Stratejik risk komitesi acil toplansın")
        if "squad_ageing" in strategic_risk.factors:
            actions.append("Kadro gençleştirme planı hızlandırılsın")
        if "contract_exposure" in strategic_risk.factors:
            actions.append("Sözleşme yenileme ve satış takvimi oluşturulsun")
        if snapshot.academy_score < 0.55:
            actions.append("Akademi yatırım ve oyuncu geçiş planı gözden geçirilsin")
        if not actions:
            actions.append("Mevcut stratejik plan kontrollü biçimde sürdürülsün")

        if health_score >= 0.75 and strategic_risk.level == "CONTROLLED":
            status = "HEALTHY"
        elif health_score >= 0.58:
            status = "WATCH"
        else:
            status = "INTERVENTION_REQUIRED"

        return ExecutiveDecisionReport(
            club_id=snapshot.club_id,
            health_score=health_score,
            objective_progress=objective_progress,
            financial_stability=financial.stability_score,
            strategic_risk=strategic_risk.score,
            priority_actions=tuple(actions),
            status=status,
        )
