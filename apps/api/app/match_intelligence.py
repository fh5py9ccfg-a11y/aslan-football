from __future__ import annotations

from dataclasses import dataclass
import json
import hashlib
import math
import time


@dataclass(frozen=True)
class TeamProfile:
    profile_id: str
    club_id: str
    team_name: str
    attack_rating: float
    defence_rating: float
    form_rating: float
    home_rating: float
    away_rating: float
    goals_for_average: float
    goals_against_average: float
    sample_size: int
    elo_rating: float = 1500.0
    xg_for_average: float = 0.0
    xg_against_average: float = 0.0
    updated_at: int = 0


@dataclass(frozen=True)
class MatchPrediction:
    prediction_id: str
    club_id: str
    match_id: str
    opponent_profile_id: str
    home_team: str
    away_team: str
    expected_home_goals: float
    expected_away_goals: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    predicted_home_goals: int
    predicted_away_goals: int
    confidence: str
    likely_scores: tuple[dict, ...]
    factors: tuple[str, ...]
    risks: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class ReleaseGateReport:
    gate_id: str
    club_id: str
    model_version: str
    tests_passed: bool
    minimum_data_ready: bool
    calibration_ready: bool
    backtest_ready: bool
    reproducibility_ready: bool
    active_model_ready: bool
    overall_status: str
    score: float
    blockers: tuple[str, ...]
    warnings: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class PipelineRunReport:
    run_id: str
    club_id: str
    match_id: str
    prediction_id: str
    data_quality_score: float
    alerts: int
    approval_status: str
    decision_report_id: str
    release_gate_status: str
    duration_ms: int
    generated_at: int


@dataclass(frozen=True)
class PilotReadinessReport:
    report_id: str
    club_id: str
    users_ready: bool
    squad_ready: bool
    fixtures_ready: bool
    prediction_ready: bool
    model_monitoring_ready: bool
    documentation_ready: bool
    operational_score: float
    status: str
    action_items: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class WalkForwardReport:
    report_id: str
    club_id: str
    competition: str
    evaluated_matches: int
    warmup_matches: int
    result_accuracy: float
    exact_score_accuracy: float
    mean_goal_error: float
    mean_brier_score: float
    leakage_checks_passed: bool
    model_version: str
    generated_at: int


@dataclass(frozen=True)
class ReproducibilityRecord:
    record_id: str
    prediction_id: str
    input_fingerprint: str
    output_fingerprint: str
    model_version: str
    deterministic: bool
    created_at: int


@dataclass(frozen=True)
class SeasonPerformanceReport:
    report_id: str
    club_id: str
    competition: str
    season_key: str
    matches: int
    result_accuracy: float
    exact_score_accuracy: float
    mean_goal_error: float
    mean_brier_score: float
    reliability_grade: str
    recalibration_recommended: bool
    generated_at: int


@dataclass(frozen=True)
class PostMatchLearningReport:
    learning_id: str
    prediction_id: str
    club_id: str
    actual_home_goals: int
    actual_away_goals: int
    result_error: bool
    score_error: float
    xg_bias_home: float
    xg_bias_away: float
    probability_overconfidence: float
    root_causes: tuple[str, ...]
    recommended_actions: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class OpponentMemory:
    memory_id: str
    club_id: str
    opponent_name: str
    matches: int
    goals_for_average: float
    goals_against_average: float
    result_points_average: float
    home_matches: int
    away_matches: int
    volatility: float
    last_updated_at: int


@dataclass(frozen=True)
class SimilarMatch:
    match_id: str
    opponent: str
    venue: str
    competition: str
    similarity_score: float
    goals_for: int
    goals_against: int
    result: str


@dataclass(frozen=True)
class BenchmarkReport:
    benchmark_id: str
    club_id: str
    evaluated_predictions: int
    model_brier_score: float
    home_always_brier_score: float
    uniform_brier_score: float
    model_result_accuracy: float
    home_always_accuracy: float
    model_skill_score: float
    verdict: str
    generated_at: int


@dataclass(frozen=True)
class ReliabilityBucket:
    bucket: str
    lower_bound: float
    upper_bound: float
    predictions: int
    mean_confidence: float
    observed_frequency: float
    calibration_gap: float


@dataclass(frozen=True)
class ReliabilityReport:
    report_id: str
    club_id: str
    buckets: tuple[dict, ...]
    expected_calibration_error: float
    maximum_calibration_error: float
    reliability_grade: str
    generated_at: int


@dataclass(frozen=True)
class PredictionAuditEvent:
    event_id: str
    prediction_id: str
    club_id: str
    event_type: str
    actor: str
    details: str
    created_at: int


@dataclass(frozen=True)
class PredictionDecision:
    decision_id: str
    prediction_id: str
    club_id: str
    status: str
    reviewer: str
    note: str
    decided_at: int


@dataclass(frozen=True)
class PredictionAlert:
    alert_id: str
    prediction_id: str
    club_id: str
    severity: str
    alert_type: str
    message: str
    acknowledged: bool
    created_at: int


@dataclass(frozen=True)
class MatchDecisionReport:
    report_id: str
    prediction_id: str
    club_id: str
    headline: str
    recommended_result: str
    predicted_score: str
    expected_goals: str
    confidence: str
    data_quality_score: float
    key_factors: tuple[str, ...]
    key_risks: tuple[str, ...]
    tactical_focus: tuple[str, ...]
    approval_status: str
    generated_at: int


@dataclass(frozen=True)
class ModelRegistryEntry:
    model_id: str
    club_id: str
    model_version: str
    status: str
    competition: str
    feature_set: tuple[str, ...]
    training_sample_size: int
    validation_brier_score: float
    validation_log_loss: float
    promoted_at: int
    created_at: int


@dataclass(frozen=True)
class PredictionSnapshot:
    snapshot_id: str
    prediction_id: str
    model_id: str
    home_probability: float
    draw_probability: float
    away_probability: float
    expected_home_goals: float
    expected_away_goals: float
    data_quality_score: float
    created_at: int


@dataclass(frozen=True)
class DriftReport:
    drift_id: str
    club_id: str
    model_id: str
    window_size: int
    result_accuracy_change: float
    brier_score_change: float
    mean_goal_error_change: float
    probability_shift: float
    drift_level: str
    warnings: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class MatchContextReport:
    context_id: str
    club_id: str
    match_id: str
    league_strength: float
    rest_days: int
    opponent_rest_days: int
    travel_km: float
    temperature_c: float
    wind_kmh: float
    precipitation_mm: float
    referee_card_rate: float
    fatigue_modifier: float
    travel_modifier: float
    weather_home_modifier: float
    weather_away_modifier: float
    referee_variance_modifier: float
    warnings: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class LiveMatchState:
    state_id: str
    prediction_id: str
    minute: int
    home_goals: int
    away_goals: int
    home_red_cards: int
    away_red_cards: int
    home_xg_live: float
    away_xg_live: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    next_goal_home_probability: float
    next_goal_away_probability: float
    generated_at: int


@dataclass(frozen=True)
class ExplainabilityReport:
    report_id: str
    prediction_id: str
    contributions: tuple[dict, ...]
    strongest_positive_factor: str
    strongest_negative_factor: str
    narrative: str
    generated_at: int


@dataclass(frozen=True)
class LineupImpactReport:
    report_id: str
    club_id: str
    match_id: str
    selected_player_ids: tuple[str, ...]
    starter_strength: float
    bench_strength: float
    attack_modifier: float
    defence_modifier: float
    availability_penalty: float
    cohesion_score: float
    warnings: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class TacticalMatchup:
    matchup_id: str
    club_id: str
    match_id: str
    own_style: str
    opponent_style: str
    possession_modifier: float
    transition_modifier: float
    pressing_modifier: float
    set_piece_modifier: float
    net_home_xg_modifier: float
    net_away_xg_modifier: float
    notes: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class MonteCarloSimulation:
    simulation_id: str
    prediction_id: str
    iterations: int
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    both_teams_score_probability: float
    over_2_5_probability: float
    under_2_5_probability: float
    first_half_home_probability: float
    first_half_draw_probability: float
    first_half_away_probability: float
    average_home_goals: float
    average_away_goals: float
    score_distribution: tuple[dict, ...]
    generated_at: int


@dataclass(frozen=True)
class DataQualityReport:
    report_id: str
    club_id: str
    club_profile_id: str
    opponent_profile_id: str
    club_sample_score: float
    opponent_sample_score: float
    xg_coverage_score: float
    availability_coverage_score: float
    recency_score: float
    overall_score: float
    grade: str
    warnings: tuple[str, ...]
    generated_at: int


@dataclass(frozen=True)
class EnsemblePrediction:
    ensemble_id: str
    prediction_id: str
    poisson_home_probability: float
    poisson_draw_probability: float
    poisson_away_probability: float
    elo_home_probability: float
    elo_draw_probability: float
    elo_away_probability: float
    blended_home_probability: float
    blended_draw_probability: float
    blended_away_probability: float
    home_probability_interval: tuple[float, float]
    draw_probability_interval: tuple[float, float]
    away_probability_interval: tuple[float, float]
    data_quality_score: float
    created_at: int


@dataclass(frozen=True)
class ModelCalibration:
    calibration_id: str
    club_id: str
    model_version: str
    elo_weight: float
    form_weight: float
    xg_weight: float
    availability_weight: float
    brier_score: float
    log_loss: float
    sample_size: int
    created_at: int


@dataclass(frozen=True)
class ScenarioPrediction:
    scenario_id: str
    prediction_id: str
    label: str
    unavailable_impact: float
    opponent_unavailable_impact: float
    expected_home_goals: float
    expected_away_goals: float
    home_win_probability: float
    draw_probability: float
    away_win_probability: float
    created_at: int


@dataclass(frozen=True)
class PredictionEvaluation:
    evaluation_id: str
    prediction_id: str
    actual_home_goals: int
    actual_away_goals: int
    result_correct: bool
    exact_score_correct: bool
    goal_error: float
    evaluated_at: int


class MatchIntelligenceValidationError(ValueError):
    pass


class RedisMatchIntelligenceRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:match-intelligence",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_profile(self, item: TeamProfile) -> TeamProfile:
        self.client.setex(
            self._profile_key(item.profile_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_profile_index(item.club_id),
            item.profile_id,
        )
        return item

    def get_profile(self, profile_id: str) -> TeamProfile | None:
        payload = self.client.get(self._profile_key(profile_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return TeamProfile(**json.loads(payload))

    def list_profiles(self, club_id: str) -> tuple[TeamProfile, ...]:
        items = []
        for profile_id in self.client.smembers(
            self._club_profile_index(club_id)
        ):
            if isinstance(profile_id, bytes):
                profile_id = profile_id.decode("utf-8")
            item = self.get_profile(str(profile_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.team_name.lower())
        return tuple(items)

    def save_prediction(
        self,
        item: MatchPrediction,
    ) -> MatchPrediction:
        payload = {
            **item.__dict__,
            "likely_scores": list(item.likely_scores),
            "factors": list(item.factors),
            "risks": list(item.risks),
        }
        self.client.setex(
            self._prediction_key(item.prediction_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_prediction_index(item.club_id),
            item.prediction_id,
        )
        return item

    def get_prediction(
        self,
        prediction_id: str,
    ) -> MatchPrediction | None:
        payload = self.client.get(
            self._prediction_key(prediction_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["likely_scores"] = tuple(data["likely_scores"])
        data["factors"] = tuple(data["factors"])
        data["risks"] = tuple(data["risks"])
        return MatchPrediction(**data)

    def list_predictions(
        self,
        club_id: str,
    ) -> tuple[MatchPrediction, ...]:
        items = []
        for prediction_id in self.client.smembers(
            self._club_prediction_index(club_id)
        ):
            if isinstance(prediction_id, bytes):
                prediction_id = prediction_id.decode("utf-8")
            item = self.get_prediction(str(prediction_id))
            if item is not None:
                items.append(item)
        items.sort(
            key=lambda item: item.generated_at,
            reverse=True,
        )
        return tuple(items)

    def save_evaluation(
        self,
        item: PredictionEvaluation,
    ) -> PredictionEvaluation:
        self.client.setex(
            self._evaluation_key(item.evaluation_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._prediction_evaluation_index(item.prediction_id),
            item.evaluation_id,
        )
        return item

    def list_evaluations(
        self,
        prediction_id: str,
    ) -> tuple[PredictionEvaluation, ...]:
        items = []
        for evaluation_id in self.client.smembers(
            self._prediction_evaluation_index(prediction_id)
        ):
            if isinstance(evaluation_id, bytes):
                evaluation_id = evaluation_id.decode("utf-8")
            payload = self.client.get(
                self._evaluation_key(str(evaluation_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                PredictionEvaluation(**json.loads(payload))
            )
        items.sort(key=lambda item: item.evaluated_at)
        return tuple(items)











    def save_release_gate(
        self,
        item: ReleaseGateReport,
    ) -> ReleaseGateReport:
        payload = {
            **item.__dict__,
            "blockers": list(item.blockers),
            "warnings": list(item.warnings),
        }
        self.client.setex(
            self._release_gate_key(item.gate_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def save_pipeline_run(
        self,
        item: PipelineRunReport,
    ) -> PipelineRunReport:
        self.client.setex(
            self._pipeline_run_key(item.run_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_pipeline_run_index(item.club_id),
            item.run_id,
        )
        return item

    def list_pipeline_runs(
        self,
        club_id: str,
    ) -> tuple[PipelineRunReport, ...]:
        items = []
        for run_id in self.client.smembers(
            self._club_pipeline_run_index(club_id)
        ):
            if isinstance(run_id, bytes):
                run_id = run_id.decode("utf-8")
            payload = self.client.get(
                self._pipeline_run_key(str(run_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                PipelineRunReport(**json.loads(payload))
            )
        items.sort(key=lambda item: item.generated_at, reverse=True)
        return tuple(items)

    def save_pilot_readiness(
        self,
        item: PilotReadinessReport,
    ) -> PilotReadinessReport:
        payload = {
            **item.__dict__,
            "action_items": list(item.action_items),
        }
        self.client.setex(
            self._pilot_readiness_key(item.report_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def save_walk_forward(
        self,
        item: WalkForwardReport,
    ) -> WalkForwardReport:
        self.client.setex(
            self._walk_forward_key(item.report_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        return item

    def save_reproducibility(
        self,
        item: ReproducibilityRecord,
    ) -> ReproducibilityRecord:
        self.client.setex(
            self._reproducibility_key(item.record_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        return item

    def save_season_report(
        self,
        item: SeasonPerformanceReport,
    ) -> SeasonPerformanceReport:
        self.client.setex(
            self._season_report_key(item.report_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        return item

    def save_learning_report(
        self,
        item: PostMatchLearningReport,
    ) -> PostMatchLearningReport:
        payload = {
            **item.__dict__,
            "root_causes": list(item.root_causes),
            "recommended_actions": list(
                item.recommended_actions
            ),
        }
        self.client.setex(
            self._learning_key(item.learning_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def save_opponent_memory(
        self,
        item: OpponentMemory,
    ) -> OpponentMemory:
        self.client.setex(
            self._opponent_memory_key(item.memory_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_opponent_memory_index(
                item.club_id
            ),
            item.memory_id,
        )
        return item

    def list_opponent_memories(
        self,
        club_id: str,
    ) -> tuple[OpponentMemory, ...]:
        items = []
        for memory_id in self.client.smembers(
            self._club_opponent_memory_index(
                club_id
            )
        ):
            if isinstance(memory_id, bytes):
                memory_id = memory_id.decode("utf-8")
            payload = self.client.get(
                self._opponent_memory_key(str(memory_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                OpponentMemory(**json.loads(payload))
            )
        items.sort(
            key=lambda item: item.opponent_name.lower()
        )
        return tuple(items)

    def save_benchmark(
        self,
        item: BenchmarkReport,
    ) -> BenchmarkReport:
        self.client.setex(
            self._benchmark_key(item.benchmark_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        return item

    def save_reliability(
        self,
        item: ReliabilityReport,
    ) -> ReliabilityReport:
        payload = {
            **item.__dict__,
            "buckets": list(item.buckets),
        }
        self.client.setex(
            self._reliability_key(item.report_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def save_audit_event(
        self,
        item: PredictionAuditEvent,
    ) -> PredictionAuditEvent:
        self.client.setex(
            self._audit_event_key(item.event_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._prediction_audit_index(
                item.prediction_id
            ),
            item.event_id,
        )
        return item

    def list_audit_events(
        self,
        prediction_id: str,
    ) -> tuple[PredictionAuditEvent, ...]:
        items = []
        for event_id in self.client.smembers(
            self._prediction_audit_index(
                prediction_id
            )
        ):
            if isinstance(event_id, bytes):
                event_id = event_id.decode("utf-8")
            payload = self.client.get(
                self._audit_event_key(str(event_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                PredictionAuditEvent(**json.loads(payload))
            )
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def save_decision(
        self,
        item: PredictionDecision,
    ) -> PredictionDecision:
        self.client.setex(
            self._decision_key(item.decision_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._prediction_decision_index(
                item.prediction_id
            ),
            item.decision_id,
        )
        return item

    def list_decisions(
        self,
        prediction_id: str,
    ) -> tuple[PredictionDecision, ...]:
        items = []
        for decision_id in self.client.smembers(
            self._prediction_decision_index(
                prediction_id
            )
        ):
            if isinstance(decision_id, bytes):
                decision_id = decision_id.decode("utf-8")
            payload = self.client.get(
                self._decision_key(str(decision_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                PredictionDecision(**json.loads(payload))
            )
        items.sort(key=lambda item: item.decided_at)
        return tuple(items)

    def save_alert(
        self,
        item: PredictionAlert,
    ) -> PredictionAlert:
        self.client.setex(
            self._alert_key(item.alert_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_alert_index(item.club_id),
            item.alert_id,
        )
        return item

    def list_alerts(
        self,
        club_id: str,
    ) -> tuple[PredictionAlert, ...]:
        items = []
        for alert_id in self.client.smembers(
            self._club_alert_index(club_id)
        ):
            if isinstance(alert_id, bytes):
                alert_id = alert_id.decode("utf-8")
            payload = self.client.get(
                self._alert_key(str(alert_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                PredictionAlert(**json.loads(payload))
            )
        items.sort(key=lambda item: item.created_at, reverse=True)
        return tuple(items)

    def save_decision_report(
        self,
        item: MatchDecisionReport,
    ) -> MatchDecisionReport:
        payload = {
            **item.__dict__,
            "key_factors": list(item.key_factors),
            "key_risks": list(item.key_risks),
            "tactical_focus": list(item.tactical_focus),
        }
        self.client.setex(
            self._decision_report_key(item.report_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def save_model(
        self,
        item: ModelRegistryEntry,
    ) -> ModelRegistryEntry:
        payload = {
            **item.__dict__,
            "feature_set": list(item.feature_set),
        }
        self.client.setex(
            self._model_key(item.model_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_model_index(item.club_id),
            item.model_id,
        )
        return item

    def get_model(
        self,
        model_id: str,
    ) -> ModelRegistryEntry | None:
        payload = self.client.get(
            self._model_key(model_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["feature_set"] = tuple(data["feature_set"])
        return ModelRegistryEntry(**data)

    def list_models(
        self,
        club_id: str,
    ) -> tuple[ModelRegistryEntry, ...]:
        items = []
        for model_id in self.client.smembers(
            self._club_model_index(club_id)
        ):
            if isinstance(model_id, bytes):
                model_id = model_id.decode("utf-8")
            item = self.get_model(str(model_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.created_at, reverse=True)
        return tuple(items)

    def save_snapshot(
        self,
        item: PredictionSnapshot,
    ) -> PredictionSnapshot:
        self.client.setex(
            self._snapshot_key(item.snapshot_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._prediction_snapshot_index(
                item.prediction_id
            ),
            item.snapshot_id,
        )
        return item

    def list_snapshots(
        self,
        prediction_id: str,
    ) -> tuple[PredictionSnapshot, ...]:
        items = []
        for snapshot_id in self.client.smembers(
            self._prediction_snapshot_index(
                prediction_id
            )
        ):
            if isinstance(snapshot_id, bytes):
                snapshot_id = snapshot_id.decode("utf-8")
            payload = self.client.get(
                self._snapshot_key(str(snapshot_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                PredictionSnapshot(**json.loads(payload))
            )
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def save_drift(
        self,
        item: DriftReport,
    ) -> DriftReport:
        payload = {
            **item.__dict__,
            "warnings": list(item.warnings),
        }
        self.client.setex(
            self._drift_key(item.drift_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def save_match_context(
        self,
        item: MatchContextReport,
    ) -> MatchContextReport:
        payload = {
            **item.__dict__,
            "warnings": list(item.warnings),
        }
        self.client.setex(
            self._match_context_key(item.context_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def get_match_context(
        self,
        context_id: str,
    ) -> MatchContextReport | None:
        payload = self.client.get(
            self._match_context_key(context_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["warnings"] = tuple(data["warnings"])
        return MatchContextReport(**data)

    def save_live_state(
        self,
        item: LiveMatchState,
    ) -> LiveMatchState:
        self.client.setex(
            self._live_state_key(item.state_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._prediction_live_state_index(
                item.prediction_id
            ),
            item.state_id,
        )
        return item

    def list_live_states(
        self,
        prediction_id: str,
    ) -> tuple[LiveMatchState, ...]:
        items = []
        for state_id in self.client.smembers(
            self._prediction_live_state_index(
                prediction_id
            )
        ):
            if isinstance(state_id, bytes):
                state_id = state_id.decode("utf-8")
            payload = self.client.get(
                self._live_state_key(str(state_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(LiveMatchState(**json.loads(payload)))
        items.sort(key=lambda item: item.minute)
        return tuple(items)

    def save_explainability(
        self,
        item: ExplainabilityReport,
    ) -> ExplainabilityReport:
        payload = {
            **item.__dict__,
            "contributions": list(item.contributions),
        }
        self.client.setex(
            self._explainability_key(item.report_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def save_lineup_report(
        self,
        item: LineupImpactReport,
    ) -> LineupImpactReport:
        payload = {
            **item.__dict__,
            "selected_player_ids": list(
                item.selected_player_ids
            ),
            "warnings": list(item.warnings),
        }
        self.client.setex(
            self._lineup_report_key(item.report_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def get_lineup_report(
        self,
        report_id: str,
    ) -> LineupImpactReport | None:
        payload = self.client.get(
            self._lineup_report_key(report_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["selected_player_ids"] = tuple(
            data["selected_player_ids"]
        )
        data["warnings"] = tuple(data["warnings"])
        return LineupImpactReport(**data)

    def save_tactical_matchup(
        self,
        item: TacticalMatchup,
    ) -> TacticalMatchup:
        payload = {
            **item.__dict__,
            "notes": list(item.notes),
        }
        self.client.setex(
            self._tactical_key(item.matchup_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def get_tactical_matchup(
        self,
        matchup_id: str,
    ) -> TacticalMatchup | None:
        payload = self.client.get(
            self._tactical_key(matchup_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["notes"] = tuple(data["notes"])
        return TacticalMatchup(**data)

    def save_simulation(
        self,
        item: MonteCarloSimulation,
    ) -> MonteCarloSimulation:
        payload = {
            **item.__dict__,
            "score_distribution": list(
                item.score_distribution
            ),
        }
        self.client.setex(
            self._simulation_key(item.simulation_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        self.client.sadd(
            self._prediction_simulation_index(
                item.prediction_id
            ),
            item.simulation_id,
        )
        return item

    def list_simulations(
        self,
        prediction_id: str,
    ) -> tuple[MonteCarloSimulation, ...]:
        items = []
        for simulation_id in self.client.smembers(
            self._prediction_simulation_index(
                prediction_id
            )
        ):
            if isinstance(simulation_id, bytes):
                simulation_id = simulation_id.decode("utf-8")
            payload = self.client.get(
                self._simulation_key(str(simulation_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            data["score_distribution"] = tuple(
                data["score_distribution"]
            )
            items.append(MonteCarloSimulation(**data))
        items.sort(key=lambda item: item.generated_at)
        return tuple(items)

    def save_data_quality(
        self,
        item: DataQualityReport,
    ) -> DataQualityReport:
        payload = {
            **item.__dict__,
            "warnings": list(item.warnings),
        }
        self.client.setex(
            self._data_quality_key(item.report_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        return item

    def get_data_quality(
        self,
        report_id: str,
    ) -> DataQualityReport | None:
        payload = self.client.get(
            self._data_quality_key(report_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["warnings"] = tuple(data["warnings"])
        return DataQualityReport(**data)

    def save_ensemble(
        self,
        item: EnsemblePrediction,
    ) -> EnsemblePrediction:
        payload = {
            **item.__dict__,
            "home_probability_interval": list(
                item.home_probability_interval
            ),
            "draw_probability_interval": list(
                item.draw_probability_interval
            ),
            "away_probability_interval": list(
                item.away_probability_interval
            ),
        }
        self.client.setex(
            self._ensemble_key(item.ensemble_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        self.client.sadd(
            self._prediction_ensemble_index(
                item.prediction_id
            ),
            item.ensemble_id,
        )
        return item

    def list_ensembles(
        self,
        prediction_id: str,
    ) -> tuple[EnsemblePrediction, ...]:
        items = []
        for ensemble_id in self.client.smembers(
            self._prediction_ensemble_index(
                prediction_id
            )
        ):
            if isinstance(ensemble_id, bytes):
                ensemble_id = ensemble_id.decode("utf-8")
            payload = self.client.get(
                self._ensemble_key(str(ensemble_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            data = json.loads(payload)
            data["home_probability_interval"] = tuple(
                data["home_probability_interval"]
            )
            data["draw_probability_interval"] = tuple(
                data["draw_probability_interval"]
            )
            data["away_probability_interval"] = tuple(
                data["away_probability_interval"]
            )
            items.append(EnsemblePrediction(**data))
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def save_calibration(
        self,
        item: ModelCalibration,
    ) -> ModelCalibration:
        self.client.setex(
            self._calibration_key(item.calibration_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_calibration_index(item.club_id),
            item.calibration_id,
        )
        return item

    def list_calibrations(
        self,
        club_id: str,
    ) -> tuple[ModelCalibration, ...]:
        items = []
        for calibration_id in self.client.smembers(
            self._club_calibration_index(club_id)
        ):
            if isinstance(calibration_id, bytes):
                calibration_id = calibration_id.decode("utf-8")
            payload = self.client.get(
                self._calibration_key(str(calibration_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(ModelCalibration(**json.loads(payload)))
        items.sort(key=lambda item: item.created_at, reverse=True)
        return tuple(items)

    def save_scenario(
        self,
        item: ScenarioPrediction,
    ) -> ScenarioPrediction:
        self.client.setex(
            self._scenario_key(item.scenario_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._prediction_scenario_index(item.prediction_id),
            item.scenario_id,
        )
        return item

    def list_scenarios(
        self,
        prediction_id: str,
    ) -> tuple[ScenarioPrediction, ...]:
        items = []
        for scenario_id in self.client.smembers(
            self._prediction_scenario_index(prediction_id)
        ):
            if isinstance(scenario_id, bytes):
                scenario_id = scenario_id.decode("utf-8")
            payload = self.client.get(
                self._scenario_key(str(scenario_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(ScenarioPrediction(**json.loads(payload)))
        items.sort(key=lambda item: item.created_at)
        return tuple(items)

    def _profile_key(self, profile_id: str) -> str:
        return f"{self.prefix}:profile:{profile_id}"

    def _club_profile_index(self, club_id: str) -> str:
        return f"{self.prefix}:profiles:{club_id}"

    def _prediction_key(self, prediction_id: str) -> str:
        return f"{self.prefix}:prediction:{prediction_id}"

    def _club_prediction_index(self, club_id: str) -> str:
        return f"{self.prefix}:predictions:{club_id}"

    def _evaluation_key(self, evaluation_id: str) -> str:
        return f"{self.prefix}:evaluation:{evaluation_id}"

    def _prediction_evaluation_index(
        self,
        prediction_id: str,
    ) -> str:
        return f"{self.prefix}:evaluations:{prediction_id}"

    def _calibration_key(self, calibration_id: str) -> str:
        return f"{self.prefix}:calibration:{calibration_id}"

    def _club_calibration_index(self, club_id: str) -> str:
        return f"{self.prefix}:calibrations:{club_id}"

    def _scenario_key(self, scenario_id: str) -> str:
        return f"{self.prefix}:scenario:{scenario_id}"

    def _prediction_scenario_index(self, prediction_id: str) -> str:
        return f"{self.prefix}:scenarios:{prediction_id}"

    def _data_quality_key(self, report_id: str) -> str:
        return f"{self.prefix}:data-quality:{report_id}"

    def _ensemble_key(self, ensemble_id: str) -> str:
        return f"{self.prefix}:ensemble:{ensemble_id}"

    def _prediction_ensemble_index(self, prediction_id: str) -> str:
        return f"{self.prefix}:ensembles:{prediction_id}"

    def _lineup_report_key(self, report_id: str) -> str:
        return f"{self.prefix}:lineup-report:{report_id}"

    def _tactical_key(self, matchup_id: str) -> str:
        return f"{self.prefix}:tactical:{matchup_id}"

    def _simulation_key(self, simulation_id: str) -> str:
        return f"{self.prefix}:simulation:{simulation_id}"

    def _prediction_simulation_index(
        self,
        prediction_id: str,
    ) -> str:
        return f"{self.prefix}:simulations:{prediction_id}"

    def _match_context_key(self, context_id: str) -> str:
        return f"{self.prefix}:context:{context_id}"

    def _live_state_key(self, state_id: str) -> str:
        return f"{self.prefix}:live-state:{state_id}"

    def _prediction_live_state_index(
        self,
        prediction_id: str,
    ) -> str:
        return f"{self.prefix}:live-states:{prediction_id}"

    def _explainability_key(self, report_id: str) -> str:
        return f"{self.prefix}:explainability:{report_id}"

    def _model_key(self, model_id: str) -> str:
        return f"{self.prefix}:model:{model_id}"

    def _club_model_index(self, club_id: str) -> str:
        return f"{self.prefix}:models:{club_id}"

    def _snapshot_key(self, snapshot_id: str) -> str:
        return f"{self.prefix}:snapshot:{snapshot_id}"

    def _prediction_snapshot_index(
        self,
        prediction_id: str,
    ) -> str:
        return f"{self.prefix}:snapshots:{prediction_id}"

    def _drift_key(self, drift_id: str) -> str:
        return f"{self.prefix}:drift:{drift_id}"

    def _decision_key(self, decision_id: str) -> str:
        return f"{self.prefix}:decision:{decision_id}"

    def _prediction_decision_index(
        self,
        prediction_id: str,
    ) -> str:
        return f"{self.prefix}:decisions:{prediction_id}"

    def _alert_key(self, alert_id: str) -> str:
        return f"{self.prefix}:alert:{alert_id}"

    def _club_alert_index(self, club_id: str) -> str:
        return f"{self.prefix}:alerts:{club_id}"

    def _decision_report_key(self, report_id: str) -> str:
        return f"{self.prefix}:decision-report:{report_id}"

    def _benchmark_key(self, benchmark_id: str) -> str:
        return f"{self.prefix}:benchmark:{benchmark_id}"

    def _reliability_key(self, report_id: str) -> str:
        return f"{self.prefix}:reliability:{report_id}"

    def _audit_event_key(self, event_id: str) -> str:
        return f"{self.prefix}:audit-event:{event_id}"

    def _prediction_audit_index(
        self,
        prediction_id: str,
    ) -> str:
        return f"{self.prefix}:audit-events:{prediction_id}"

    def _learning_key(self, learning_id: str) -> str:
        return f"{self.prefix}:learning:{learning_id}"

    def _opponent_memory_key(self, memory_id: str) -> str:
        return f"{self.prefix}:opponent-memory:{memory_id}"

    def _club_opponent_memory_index(
        self,
        club_id: str,
    ) -> str:
        return f"{self.prefix}:opponent-memories:{club_id}"

    def _walk_forward_key(self, report_id: str) -> str:
        return f"{self.prefix}:walk-forward:{report_id}"

    def _reproducibility_key(self, record_id: str) -> str:
        return f"{self.prefix}:reproducibility:{record_id}"

    def _season_report_key(self, report_id: str) -> str:
        return f"{self.prefix}:season-report:{report_id}"

    def _release_gate_key(self, gate_id: str) -> str:
        return f"{self.prefix}:release-gate:{gate_id}"

    def _pipeline_run_key(self, run_id: str) -> str:
        return f"{self.prefix}:pipeline-run:{run_id}"

    def _club_pipeline_run_index(self, club_id: str) -> str:
        return f"{self.prefix}:pipeline-runs:{club_id}"

    def _pilot_readiness_key(self, report_id: str) -> str:
        return f"{self.prefix}:pilot-readiness:{report_id}"


class MatchIntelligenceService:
    def __init__(
        self,
        *,
        repository,
        workspace_service,
    ):
        self.repository = repository
        self.workspace_service = workspace_service

    def derive_club_profile(
        self,
        *,
        profile_id: str,
        club_id: str,
        now: int | None = None,
    ) -> TeamProfile:
        club = self.workspace_service.repository.get_club(club_id)
        if club is None:
            raise KeyError("Kulüp bulunamadı")

        completed = [
            item
            for item in self.workspace_service.repository.list_matches(club_id)
            if item.status == "COMPLETED"
        ]
        if not completed:
            goals_for_average = 1.20
            goals_against_average = 1.20
            form_rating = 0.50
            home_rating = 0.50
            away_rating = 0.50
        else:
            recent = completed[-12:]
            weights = [
                0.85 ** (len(recent) - index - 1)
                for index in range(len(recent))
            ]
            weight_sum = sum(weights)
            goals_for_average = sum(
                (item.goals_for or 0) * weights[index]
                for index, item in enumerate(recent)
            ) / weight_sum
            goals_against_average = sum(
                (item.goals_against or 0) * weights[index]
                for index, item in enumerate(recent)
            ) / weight_sum

            points = sum(
                3
                if (item.goals_for or 0) > (item.goals_against or 0)
                else 1
                if item.goals_for == item.goals_against
                else 0
                for item in completed[-5:]
            )
            form_rating = points / max(1, len(completed[-5:]) * 3)

            home_matches = [item for item in completed if item.venue == "HOME"]
            away_matches = [item for item in completed if item.venue == "AWAY"]
            home_rating = self._result_rating(home_matches)
            away_rating = self._result_rating(away_matches)

        attack_rating = self._clamp(
            goals_for_average / 1.35,
            0.45,
            1.75,
        )
        defence_rating = self._clamp(
            goals_against_average / 1.35,
            0.45,
            1.75,
        )

        item = TeamProfile(
            profile_id=profile_id,
            club_id=club_id,
            team_name=club.name,
            attack_rating=round(attack_rating, 3),
            defence_rating=round(defence_rating, 3),
            form_rating=round(form_rating, 3),
            home_rating=round(home_rating, 3),
            away_rating=round(away_rating, 3),
            goals_for_average=round(goals_for_average, 3),
            goals_against_average=round(goals_against_average, 3),
            sample_size=len(completed),
            elo_rating=round(
                self._derive_elo(completed),
                2,
            ),
            xg_for_average=round(
                goals_for_average * 0.92,
                3,
            ),
            xg_against_average=round(
                goals_against_average * 0.92,
                3,
            ),
            updated_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_profile(item)

    def save_opponent_profile(
        self,
        *,
        profile_id: str,
        club_id: str,
        team_name: str,
        attack_rating: float,
        defence_rating: float,
        form_rating: float,
        home_rating: float,
        away_rating: float,
        goals_for_average: float,
        goals_against_average: float,
        sample_size: int,
        elo_rating: float = 1500.0,
        xg_for_average: float = 0.0,
        xg_against_average: float = 0.0,
        now: int | None = None,
    ) -> TeamProfile:
        for value in (
            attack_rating,
            defence_rating,
            form_rating,
            home_rating,
            away_rating,
        ):
            if not 0 <= value <= 2:
                raise MatchIntelligenceValidationError(
                    "Takım rating değerleri 0 ile 2 arasında olmalıdır"
                )
        if goals_for_average < 0 or goals_against_average < 0:
            raise MatchIntelligenceValidationError(
                "Gol ortalamaları negatif olamaz"
            )
        item = TeamProfile(
            profile_id=profile_id,
            club_id=club_id,
            team_name=team_name.strip(),
            attack_rating=attack_rating,
            defence_rating=defence_rating,
            form_rating=form_rating,
            home_rating=home_rating,
            away_rating=away_rating,
            goals_for_average=goals_for_average,
            goals_against_average=goals_against_average,
            sample_size=sample_size,
            elo_rating=elo_rating,
            xg_for_average=xg_for_average,
            xg_against_average=xg_against_average,
            updated_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_profile(item)

    def predict(
        self,
        *,
        prediction_id: str,
        club_id: str,
        match_id: str,
        club_profile_id: str,
        opponent_profile_id: str,
        unavailable_impact: float = 0.0,
        opponent_unavailable_impact: float = 0.0,
        now: int | None = None,
    ) -> MatchPrediction:
        match = next(
            (
                item
                for item in self.workspace_service.repository.list_matches(
                    club_id
                )
                if item.match_id == match_id
            ),
            None,
        )
        if match is None:
            raise KeyError("Maç bulunamadı")

        club_profile = self.repository.get_profile(club_profile_id)
        opponent = self.repository.get_profile(opponent_profile_id)
        if club_profile is None or opponent is None:
            raise KeyError("Takım güç profili bulunamadı")

        if not 0 <= unavailable_impact <= 0.70:
            raise MatchIntelligenceValidationError(
                "Eksik oyuncu etkisi 0 ile 0.70 arasında olmalıdır"
            )
        if not 0 <= opponent_unavailable_impact <= 0.70:
            raise MatchIntelligenceValidationError(
                "Rakip eksik etkisi 0 ile 0.70 arasında olmalıdır"
            )

        is_home = match.venue == "HOME"
        home_profile = club_profile if is_home else opponent
        away_profile = opponent if is_home else club_profile
        home_unavailable = (
            unavailable_impact
            if is_home
            else opponent_unavailable_impact
        )
        away_unavailable = (
            opponent_unavailable_impact
            if is_home
            else unavailable_impact
        )

        home_xg = self._expected_goals(
            attack=home_profile.attack_rating,
            elo=home_profile.elo_rating,
            opponent_elo=away_profile.elo_rating,
            xg_for=home_profile.xg_for_average,
            xg_against=away_profile.xg_against_average,
            opponent_defence=away_profile.defence_rating,
            form=home_profile.form_rating,
            venue_rating=home_profile.home_rating,
            unavailable=home_unavailable,
            opponent_unavailable=away_unavailable,
            home_advantage=1.14,
        )
        away_xg = self._expected_goals(
            attack=away_profile.attack_rating,
            elo=away_profile.elo_rating,
            opponent_elo=home_profile.elo_rating,
            xg_for=away_profile.xg_for_average,
            xg_against=home_profile.xg_against_average,
            opponent_defence=home_profile.defence_rating,
            form=away_profile.form_rating,
            venue_rating=away_profile.away_rating,
            unavailable=away_unavailable,
            opponent_unavailable=home_unavailable,
            home_advantage=0.94,
        )

        matrix = []
        home_win = draw = away_win = 0.0
        for home_goals in range(0, 8):
            for away_goals in range(0, 8):
                probability = (
                    self._poisson(home_goals, home_xg)
                    * self._poisson(away_goals, away_xg)
                )
                matrix.append({
                    "home_goals": home_goals,
                    "away_goals": away_goals,
                    "probability": probability,
                })
                if home_goals > away_goals:
                    home_win += probability
                elif home_goals == away_goals:
                    draw += probability
                else:
                    away_win += probability

        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total
        matrix.sort(
            key=lambda item: item["probability"],
            reverse=True,
        )
        likely_scores = tuple(
            {
                "score": f"{item['home_goals']}-{item['away_goals']}",
                "probability": round(item["probability"] * 100, 2),
            }
            for item in matrix[:5]
        )
        best = matrix[0]

        factors = self._explain(
            match=match,
            club_profile=club_profile,
            opponent=opponent,
            unavailable_impact=unavailable_impact,
            opponent_unavailable_impact=opponent_unavailable_impact,
            home_xg=home_xg,
            away_xg=away_xg,
        )
        risks = self._risks(
            club_profile=club_profile,
            opponent=opponent,
            unavailable_impact=unavailable_impact,
        )
        max_probability = max(home_win, draw, away_win)
        confidence = (
            "HIGH"
            if max_probability >= 0.60 and min(
                club_profile.sample_size,
                opponent.sample_size,
            ) >= 8
            else "MEDIUM"
            if max_probability >= 0.45
            else "LOW"
        )

        item = MatchPrediction(
            prediction_id=prediction_id,
            club_id=club_id,
            match_id=match_id,
            opponent_profile_id=opponent_profile_id,
            home_team=home_profile.team_name,
            away_team=away_profile.team_name,
            expected_home_goals=round(home_xg, 2),
            expected_away_goals=round(away_xg, 2),
            home_win_probability=round(home_win * 100, 2),
            draw_probability=round(draw * 100, 2),
            away_win_probability=round(away_win * 100, 2),
            predicted_home_goals=best["home_goals"],
            predicted_away_goals=best["away_goals"],
            confidence=confidence,
            likely_scores=likely_scores,
            factors=tuple(factors),
            risks=tuple(risks),
            generated_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_prediction(item)

    def evaluate(
        self,
        *,
        evaluation_id: str,
        prediction_id: str,
        actual_home_goals: int,
        actual_away_goals: int,
        now: int | None = None,
    ) -> PredictionEvaluation:
        prediction = self.repository.get_prediction(prediction_id)
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")
        if actual_home_goals < 0 or actual_away_goals < 0:
            raise MatchIntelligenceValidationError(
                "Gerçek skor negatif olamaz"
            )
        predicted_result = self._result(
            prediction.predicted_home_goals,
            prediction.predicted_away_goals,
        )
        actual_result = self._result(
            actual_home_goals,
            actual_away_goals,
        )
        item = PredictionEvaluation(
            evaluation_id=evaluation_id,
            prediction_id=prediction_id,
            actual_home_goals=actual_home_goals,
            actual_away_goals=actual_away_goals,
            result_correct=predicted_result == actual_result,
            exact_score_correct=(
                prediction.predicted_home_goals == actual_home_goals
                and prediction.predicted_away_goals == actual_away_goals
            ),
            goal_error=round(
                (
                    abs(
                        prediction.expected_home_goals
                        - actual_home_goals
                    )
                    + abs(
                        prediction.expected_away_goals
                        - actual_away_goals
                    )
                )
                / 2,
                3,
            ),
            evaluated_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_evaluation(item)

    def accuracy_report(self, *, club_id: str) -> dict:
        predictions = self.repository.list_predictions(club_id)
        evaluations = [
            evaluation
            for prediction in predictions
            for evaluation in self.repository.list_evaluations(
                prediction.prediction_id
            )
        ]
        total = len(evaluations)
        if total == 0:
            return {
                "club_id": club_id,
                "evaluated_predictions": 0,
                "result_accuracy": 0.0,
                "exact_score_accuracy": 0.0,
                "mean_goal_error": 0.0,
            }
        return {
            "club_id": club_id,
            "evaluated_predictions": total,
            "result_accuracy": round(
                sum(1 for item in evaluations if item.result_correct)
                / total
                * 100,
                2,
            ),
            "exact_score_accuracy": round(
                sum(1 for item in evaluations if item.exact_score_correct)
                / total
                * 100,
                2,
            ),
            "mean_goal_error": round(
                sum(item.goal_error for item in evaluations) / total,
                3,
            ),
        }











    def release_gate(
        self,
        *,
        gate_id: str,
        club_id: str,
        model_version: str = "build-015",
        tests_passed: bool = True,
        documentation_ready: bool = True,
        now: int | None = None,
    ) -> ReleaseGateReport:
        players = self.workspace_service.repository.list_players(
            club_id
        )
        matches = self.workspace_service.repository.list_matches(
            club_id
        )
        predictions = self.repository.list_predictions(
            club_id
        )
        models = self.repository.list_models(club_id)
        active_models = [
            item for item in models
            if item.status == "ACTIVE"
        ]
        backtest = self.rolling_backtest(
            club_id=club_id,
            window_size=20,
        )
        calibrations = self.repository.list_calibrations(
            club_id
        )

        minimum_data_ready = (
            len(players) >= 11
            and len(matches) >= 1
        )
        calibration_ready = (
            bool(calibrations)
            or backtest["evaluated"] < 5
        )
        backtest_ready = (
            backtest["evaluated"] >= 5
            and backtest["mean_brier_score"] <= 0.85
        ) or backtest["evaluated"] == 0
        reproducibility_ready = True
        if predictions:
            sample = predictions[0]
            reproducibility = self.reproducibility_record(
                record_id=f"{gate_id}:repro",
                prediction_id=sample.prediction_id,
                model_version=model_version,
                now=now,
            )
            reproducibility_ready = reproducibility.deterministic
        active_model_ready = bool(active_models)

        blockers = []
        warnings = []
        if not tests_passed:
            blockers.append("Otomatik test paketi başarısız")
        if not minimum_data_ready:
            blockers.append(
                "En az 11 oyuncu ve 1 fikstür gerekli"
            )
        if not active_model_ready:
            blockers.append("Aktif model bulunamadı")
        if not reproducibility_ready:
            blockers.append(
                "Tahmin çıktıları deterministik değil"
            )
        if not backtest_ready:
            blockers.append(
                "Backtest kalite eşiği karşılanmıyor"
            )
        if not calibration_ready:
            warnings.append(
                "Model kalibrasyonu güncel değil"
            )
        if not documentation_ready:
            warnings.append(
                "Pilot kullanım dokümantasyonu eksik"
            )
        if backtest["evaluated"] < 5:
            warnings.append(
                "Backtest örneklemi düşük"
            )

        checks = (
            tests_passed,
            minimum_data_ready,
            calibration_ready,
            backtest_ready,
            reproducibility_ready,
            active_model_ready,
            documentation_ready,
        )
        score = sum(1 for item in checks if item) / len(checks) * 100
        status = (
            "GO"
            if not blockers and score >= 85
            else "CONDITIONAL_GO"
            if len(blockers) <= 1 and score >= 70
            else "NO_GO"
        )

        item = ReleaseGateReport(
            gate_id=gate_id,
            club_id=club_id,
            model_version=model_version,
            tests_passed=tests_passed,
            minimum_data_ready=minimum_data_ready,
            calibration_ready=calibration_ready,
            backtest_ready=backtest_ready,
            reproducibility_ready=reproducibility_ready,
            active_model_ready=active_model_ready,
            overall_status=status,
            score=round(score, 2),
            blockers=tuple(blockers),
            warnings=tuple(warnings),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_release_gate(item)

    def run_end_to_end_pipeline(
        self,
        *,
        run_id: str,
        club_id: str,
        match_id: str,
        club_profile_id: str,
        opponent_profile_id: str,
        reviewer: str,
        now: int | None = None,
    ) -> PipelineRunReport:
        start = time.perf_counter()
        current = int(now if now is not None else time.time())
        prediction_id = f"{run_id}:prediction"

        prediction = self.predict(
            prediction_id=prediction_id,
            club_id=club_id,
            match_id=match_id,
            club_profile_id=club_profile_id,
            opponent_profile_id=opponent_profile_id,
            unavailable_impact=self.automatic_unavailable_impact(
                club_id=club_id
            ),
            now=current,
        )
        quality = self.data_quality_report(
            report_id=f"{run_id}:quality",
            club_id=club_id,
            club_profile_id=club_profile_id,
            opponent_profile_id=opponent_profile_id,
            now=current,
        )
        alerts = self.generate_alerts(
            club_id=club_id,
            prediction_id=prediction_id,
            data_quality_score=quality.overall_score,
            now=current,
        )
        high_alerts = [
            alert for alert in alerts
            if alert.severity == "HIGH"
        ]
        approval_status = (
            "NEEDS_REVIEW"
            if high_alerts
            else "APPROVED"
        )
        self.review_prediction(
            decision_id=f"{run_id}:decision",
            prediction_id=prediction_id,
            club_id=club_id,
            status=approval_status,
            reviewer=reviewer,
            note=(
                "Yüksek seviye uyarı mevcut"
                if high_alerts
                else "Otomatik kalite kontrolleri geçti"
            ),
            now=current,
        )
        decision = self.decision_report(
            report_id=f"{run_id}:decision-report",
            prediction_id=prediction_id,
            club_id=club_id,
            data_quality_score=quality.overall_score,
            now=current,
        )
        gate = self.release_gate(
            gate_id=f"{run_id}:gate",
            club_id=club_id,
            model_version="build-015",
            tests_passed=True,
            documentation_ready=True,
            now=current,
        )
        duration_ms = int(
            (time.perf_counter() - start) * 1000
        )

        item = PipelineRunReport(
            run_id=run_id,
            club_id=club_id,
            match_id=match_id,
            prediction_id=prediction.prediction_id,
            data_quality_score=quality.overall_score,
            alerts=len(alerts),
            approval_status=decision.approval_status,
            decision_report_id=decision.report_id,
            release_gate_status=gate.overall_status,
            duration_ms=duration_ms,
            generated_at=current,
        )
        return self.repository.save_pipeline_run(item)

    def pilot_readiness(
        self,
        *,
        report_id: str,
        club_id: str,
        documentation_ready: bool = True,
        now: int | None = None,
    ) -> PilotReadinessReport:
        players = self.workspace_service.repository.list_players(
            club_id
        )
        matches = self.workspace_service.repository.list_matches(
            club_id
        )
        predictions = self.repository.list_predictions(
            club_id
        )
        models = self.repository.list_models(club_id)
        pipeline_runs = self.repository.list_pipeline_runs(
            club_id
        )

        users_ready = True
        squad_ready = len(players) >= 18
        fixtures_ready = len(matches) >= 3
        prediction_ready = bool(predictions)
        model_monitoring_ready = (
            any(model.status == "ACTIVE" for model in models)
            and bool(pipeline_runs)
        )

        checks = (
            users_ready,
            squad_ready,
            fixtures_ready,
            prediction_ready,
            model_monitoring_ready,
            documentation_ready,
        )
        score = sum(1 for value in checks if value) / len(checks) * 100

        actions = []
        if not squad_ready:
            actions.append(
                "Pilot öncesi en az 18 oyuncu kaydı tamamlanmalı"
            )
        if not fixtures_ready:
            actions.append(
                "En az 3 yaklaşan veya geçmiş fikstür girilmeli"
            )
        if not prediction_ready:
            actions.append(
                "En az bir uçtan uca tahmin pipeline'ı çalıştırılmalı"
            )
        if not model_monitoring_ready:
            actions.append(
                "Aktif model ve pipeline izleme kaydı oluşturulmalı"
            )
        if not documentation_ready:
            actions.append(
                "Pilot kullanıcı kılavuzu tamamlanmalı"
            )
        if not actions:
            actions.append(
                "Pilot kulüp kurulumu için operasyonel olarak hazır"
            )

        status = (
            "READY"
            if score >= 90
            else "PARTIALLY_READY"
            if score >= 65
            else "NOT_READY"
        )
        item = PilotReadinessReport(
            report_id=report_id,
            club_id=club_id,
            users_ready=users_ready,
            squad_ready=squad_ready,
            fixtures_ready=fixtures_ready,
            prediction_ready=prediction_ready,
            model_monitoring_ready=model_monitoring_ready,
            documentation_ready=documentation_ready,
            operational_score=round(score, 2),
            status=status,
            action_items=tuple(actions),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_pilot_readiness(item)

    def derive_opponent_profile_from_history(
        self,
        *,
        profile_id: str,
        club_id: str,
        opponent_name: str,
        cutoff_at: int,
        now: int | None = None,
    ) -> TeamProfile:
        matches = [
            match
            for match in self.workspace_service.repository.list_matches(
                club_id
            )
            if (
                match.status == "COMPLETED"
                and match.opponent.lower()
                == opponent_name.lower()
                and match.kickoff_at < cutoff_at
            )
        ]
        if not matches:
            return self.save_opponent_profile(
                profile_id=profile_id,
                club_id=club_id,
                team_name=opponent_name,
                attack_rating=1.0,
                defence_rating=1.0,
                form_rating=0.5,
                home_rating=0.5,
                away_rating=0.5,
                goals_for_average=1.3,
                goals_against_average=1.3,
                sample_size=0,
                elo_rating=1500,
                xg_for_average=1.2,
                xg_against_average=1.2,
                now=now,
            )

        # Club perspective is inverted to estimate opponent strengths.
        opponent_goals_for = [
            match.goals_against or 0
            for match in matches
        ]
        opponent_goals_against = [
            match.goals_for or 0
            for match in matches
        ]
        gf = sum(opponent_goals_for) / len(matches)
        ga = sum(opponent_goals_against) / len(matches)

        recent = matches[-5:]
        opponent_points = sum(
            3
            if (match.goals_against or 0) > (match.goals_for or 0)
            else 1
            if match.goals_against == match.goals_for
            else 0
            for match in recent
        )
        form = opponent_points / max(1, len(recent) * 3)

        return self.save_opponent_profile(
            profile_id=profile_id,
            club_id=club_id,
            team_name=opponent_name,
            attack_rating=self._clamp(gf / 1.35, 0.45, 1.75),
            defence_rating=self._clamp(ga / 1.35, 0.45, 1.75),
            form_rating=form,
            home_rating=0.5,
            away_rating=0.5,
            goals_for_average=gf,
            goals_against_average=ga,
            sample_size=len(matches),
            elo_rating=1500 + (gf - ga) * 35,
            xg_for_average=gf * 0.92,
            xg_against_average=ga * 0.92,
            now=now,
        )

    def walk_forward_backtest(
        self,
        *,
        report_id: str,
        club_id: str,
        competition: str,
        warmup_matches: int = 5,
        now: int | None = None,
    ) -> WalkForwardReport:
        if not 3 <= warmup_matches <= 30:
            raise MatchIntelligenceValidationError(
                "Warmup maç sayısı 3 ile 30 arasında olmalıdır"
            )

        matches = [
            match
            for match in self.workspace_service.repository.list_matches(
                club_id
            )
            if (
                match.status == "COMPLETED"
                and match.competition.lower()
                == competition.lower()
            )
        ]
        matches.sort(key=lambda item: item.kickoff_at)

        if len(matches) <= warmup_matches:
            raise MatchIntelligenceValidationError(
                "Walk-forward test için yeterli tamamlanmış maç yok"
            )

        rows = []
        leakage_checks_passed = True
        for index in range(warmup_matches, len(matches)):
            target = matches[index]
            historical = matches[:index]
            if any(
                item.kickoff_at >= target.kickoff_at
                for item in historical
            ):
                leakage_checks_passed = False
                continue

            gf = sum(
                item.goals_for or 0
                for item in historical
            ) / len(historical)
            ga = sum(
                item.goals_against or 0
                for item in historical
            ) / len(historical)
            recent = historical[-5:]
            points = sum(
                3
                if (item.goals_for or 0) > (item.goals_against or 0)
                else 1
                if item.goals_for == item.goals_against
                else 0
                for item in recent
            )
            form = points / max(1, len(recent) * 3)

            home_factor = 1.12 if target.venue == "HOME" else 0.94
            home_xg = self._clamp(
                1.20
                * self._clamp(gf / 1.35, 0.55, 1.55)
                * (0.85 + form * 0.30)
                * home_factor,
                0.20,
                4.0,
            )
            away_xg = self._clamp(
                1.15
                * self._clamp(ga / 1.35, 0.55, 1.55)
                / home_factor,
                0.20,
                4.0,
            )
            home_p, draw_p, away_p = self._outcome_probabilities(
                home_xg,
                away_xg,
            )
            probs = {
                "HOME": home_p,
                "DRAW": draw_p,
                "AWAY": away_p,
            }
            predicted_result = max(probs, key=probs.get)
            actual_result = self._result(
                target.goals_for or 0,
                target.goals_against or 0,
            )

            best_score = max(
                (
                    (
                        hg,
                        ag,
                        self._poisson(hg, home_xg)
                        * self._poisson(ag, away_xg),
                    )
                    for hg in range(0, 7)
                    for ag in range(0, 7)
                ),
                key=lambda item: item[2],
            )
            exact = (
                best_score[0] == (target.goals_for or 0)
                and best_score[1] == (target.goals_against or 0)
            )
            brier = sum(
                (
                    probs[result]
                    - (1.0 if result == actual_result else 0.0)
                ) ** 2
                for result in ("HOME", "DRAW", "AWAY")
            )
            rows.append({
                "result_correct": predicted_result == actual_result,
                "exact_score_correct": exact,
                "goal_error": (
                    abs(home_xg - (target.goals_for or 0))
                    + abs(away_xg - (target.goals_against or 0))
                ) / 2,
                "brier": brier,
            })

        total = len(rows)
        if total == 0:
            raise MatchIntelligenceValidationError(
                "Walk-forward test sonucu üretilemedi"
            )

        item = WalkForwardReport(
            report_id=report_id,
            club_id=club_id,
            competition=competition,
            evaluated_matches=total,
            warmup_matches=warmup_matches,
            result_accuracy=round(
                sum(1 for row in rows if row["result_correct"])
                / total * 100,
                2,
            ),
            exact_score_accuracy=round(
                sum(1 for row in rows if row["exact_score_correct"])
                / total * 100,
                2,
            ),
            mean_goal_error=round(
                sum(row["goal_error"] for row in rows)
                / total,
                3,
            ),
            mean_brier_score=round(
                sum(row["brier"] for row in rows)
                / total,
                4,
            ),
            leakage_checks_passed=leakage_checks_passed,
            model_version="build-014",
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_walk_forward(item)

    def reproducibility_record(
        self,
        *,
        record_id: str,
        prediction_id: str,
        model_version: str = "build-014",
        now: int | None = None,
    ) -> ReproducibilityRecord:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")

        input_payload = {
            "club_id": prediction.club_id,
            "match_id": prediction.match_id,
            "opponent_profile_id": prediction.opponent_profile_id,
        }
        output_payload = {
            "home_xg": prediction.expected_home_goals,
            "away_xg": prediction.expected_away_goals,
            "home": prediction.home_win_probability,
            "draw": prediction.draw_probability,
            "away": prediction.away_win_probability,
            "score": (
                prediction.predicted_home_goals,
                prediction.predicted_away_goals,
            ),
        }
        input_fingerprint = hashlib.sha256(
            json.dumps(
                input_payload,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()
        output_fingerprint = hashlib.sha256(
            json.dumps(
                output_payload,
                sort_keys=True,
            ).encode("utf-8")
        ).hexdigest()

        prior = [
            item
            for item in self.repository.list_predictions(
                prediction.club_id
            )
            if (
                item.match_id == prediction.match_id
                and item.opponent_profile_id
                == prediction.opponent_profile_id
            )
        ]
        matching_outputs = {
            (
                item.expected_home_goals,
                item.expected_away_goals,
                item.home_win_probability,
                item.draw_probability,
                item.away_win_probability,
                item.predicted_home_goals,
                item.predicted_away_goals,
            )
            for item in prior
        }
        deterministic = len(matching_outputs) <= 1

        item = ReproducibilityRecord(
            record_id=record_id,
            prediction_id=prediction_id,
            input_fingerprint=input_fingerprint,
            output_fingerprint=output_fingerprint,
            model_version=model_version,
            deterministic=deterministic,
            created_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_reproducibility(item)

    def season_performance_report(
        self,
        *,
        report_id: str,
        club_id: str,
        competition: str,
        season_key: str,
        now: int | None = None,
    ) -> SeasonPerformanceReport:
        backtest = self.rolling_backtest(
            club_id=club_id,
            window_size=100,
        )
        reliability = self.reliability_report(
            report_id=f"{report_id}:reliability",
            club_id=club_id,
            now=now,
        )
        recalibration = self.recalibration_recommendation(
            club_id=club_id
        )
        item = SeasonPerformanceReport(
            report_id=report_id,
            club_id=club_id,
            competition=competition,
            season_key=season_key,
            matches=backtest["evaluated"],
            result_accuracy=backtest["result_accuracy"],
            exact_score_accuracy=backtest[
                "exact_score_accuracy"
            ],
            mean_goal_error=backtest["mean_goal_error"],
            mean_brier_score=backtest["mean_brier_score"],
            reliability_grade=(
                reliability.reliability_grade
            ),
            recalibration_recommended=bool(
                recalibration["recommended"]
            ),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_season_report(item)

    def post_match_learning(
        self,
        *,
        learning_id: str,
        prediction_id: str,
        club_id: str,
        actual_home_goals: int,
        actual_away_goals: int,
        now: int | None = None,
    ) -> PostMatchLearningReport:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")

        predicted_result = self._result(
            prediction.predicted_home_goals,
            prediction.predicted_away_goals,
        )
        actual_result = self._result(
            actual_home_goals,
            actual_away_goals,
        )
        result_error = predicted_result != actual_result
        score_error = (
            abs(
                prediction.predicted_home_goals
                - actual_home_goals
            )
            + abs(
                prediction.predicted_away_goals
                - actual_away_goals
            )
        ) / 2
        xg_bias_home = (
            prediction.expected_home_goals
            - actual_home_goals
        )
        xg_bias_away = (
            prediction.expected_away_goals
            - actual_away_goals
        )
        actual_probability = {
            "HOME": prediction.home_win_probability,
            "DRAW": prediction.draw_probability,
            "AWAY": prediction.away_win_probability,
        }[actual_result]
        predicted_probability = max(
            prediction.home_win_probability,
            prediction.draw_probability,
            prediction.away_win_probability,
        )
        overconfidence = (
            predicted_probability - actual_probability
            if result_error
            else max(0.0, predicted_probability - 80.0)
        )

        causes = []
        actions = []
        if abs(xg_bias_home) >= 0.75:
            causes.append(
                "Ev sahibi beklenen gol tahmininde belirgin sapma"
            )
            actions.append(
                "Ev sahibi hücum ve rakip savunma ağırlıklarını yeniden kontrol et"
            )
        if abs(xg_bias_away) >= 0.75:
            causes.append(
                "Deplasman beklenen gol tahmininde belirgin sapma"
            )
            actions.append(
                "Rakip hücum gücü ve kadro eksikliği sinyallerini güncelle"
            )
        if overconfidence >= 20:
            causes.append(
                "Model sonucu gereğinden yüksek güvenle tahmin etti"
            )
            actions.append(
                "Olasılık kalibrasyonunu yeniden çalıştır"
            )
        if result_error and score_error <= 0.5:
            causes.append(
                "Skor yakın olmasına rağmen 1X2 sonucu yanlış sınıflandı"
            )
            actions.append(
                "Beraberlik olasılığı kalibrasyonunu incele"
            )
        if score_error >= 1.5:
            causes.append(
                "Gol dağılımında yüksek hata"
            )
            actions.append(
                "Poisson ortalamalarını ve lig gol ortamını yeniden kalibre et"
            )
        if not causes:
            causes.append(
                "Tahmin kabul edilebilir hata aralığında"
            )
            actions.append(
                "Mevcut model ağırlıklarını koru"
            )

        item = PostMatchLearningReport(
            learning_id=learning_id,
            prediction_id=prediction_id,
            club_id=club_id,
            actual_home_goals=actual_home_goals,
            actual_away_goals=actual_away_goals,
            result_error=result_error,
            score_error=round(score_error, 3),
            xg_bias_home=round(xg_bias_home, 3),
            xg_bias_away=round(xg_bias_away, 3),
            probability_overconfidence=round(
                overconfidence,
                2,
            ),
            root_causes=tuple(causes),
            recommended_actions=tuple(actions),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_learning_report(item)

    def rebuild_opponent_memory(
        self,
        *,
        club_id: str,
        now: int | None = None,
    ) -> tuple[OpponentMemory, ...]:
        completed = [
            match
            for match in self.workspace_service.repository.list_matches(
                club_id
            )
            if match.status == "COMPLETED"
        ]
        grouped: dict[str, list] = {}
        for match in completed:
            grouped.setdefault(
                match.opponent,
                [],
            ).append(match)

        memories = []
        current = int(now if now is not None else time.time())
        for opponent, matches in grouped.items():
            goals_for = [
                match.goals_for or 0
                for match in matches
            ]
            goals_against = [
                match.goals_against or 0
                for match in matches
            ]
            points = [
                3
                if gf > ga
                else 1
                if gf == ga
                else 0
                for gf, ga in zip(
                    goals_for,
                    goals_against,
                )
            ]
            total_goals = [
                gf + ga
                for gf, ga in zip(
                    goals_for,
                    goals_against,
                )
            ]
            mean_total = (
                sum(total_goals) / len(total_goals)
            )
            volatility = (
                sum(
                    (value - mean_total) ** 2
                    for value in total_goals
                )
                / len(total_goals)
            ) ** 0.5

            item = OpponentMemory(
                memory_id=(
                    f"{club_id}:{opponent.lower().replace(' ', '-')}"
                ),
                club_id=club_id,
                opponent_name=opponent,
                matches=len(matches),
                goals_for_average=round(
                    sum(goals_for) / len(goals_for),
                    3,
                ),
                goals_against_average=round(
                    sum(goals_against)
                    / len(goals_against),
                    3,
                ),
                result_points_average=round(
                    sum(points) / len(points),
                    3,
                ),
                home_matches=sum(
                    1
                    for match in matches
                    if match.venue == "HOME"
                ),
                away_matches=sum(
                    1
                    for match in matches
                    if match.venue == "AWAY"
                ),
                volatility=round(volatility, 3),
                last_updated_at=current,
            )
            self.repository.save_opponent_memory(item)
            memories.append(item)
        return tuple(memories)

    def similar_matches(
        self,
        *,
        club_id: str,
        match_id: str,
        limit: int = 5,
    ) -> tuple[SimilarMatch, ...]:
        matches = list(
            self.workspace_service.repository.list_matches(
                club_id
            )
        )
        target = next(
            (
                match
                for match in matches
                if match.match_id == match_id
            ),
            None,
        )
        if target is None:
            raise KeyError("Maç bulunamadı")

        candidates = [
            match
            for match in matches
            if (
                match.match_id != match_id
                and match.status == "COMPLETED"
            )
        ]
        rows = []
        for match in candidates:
            score = 0.0
            if match.venue == target.venue:
                score += 0.35
            if (
                match.competition.lower()
                == target.competition.lower()
            ):
                score += 0.35
            if (
                match.opponent.lower()
                == target.opponent.lower()
            ):
                score += 0.30
            result = self._result(
                match.goals_for or 0,
                match.goals_against or 0,
            )
            rows.append(
                SimilarMatch(
                    match_id=match.match_id,
                    opponent=match.opponent,
                    venue=match.venue,
                    competition=match.competition,
                    similarity_score=round(
                        score * 100,
                        2,
                    ),
                    goals_for=match.goals_for or 0,
                    goals_against=match.goals_against or 0,
                    result=result,
                )
            )
        rows.sort(
            key=lambda item: item.similarity_score,
            reverse=True,
        )
        return tuple(rows[:limit])

    def recalibration_recommendation(
        self,
        *,
        club_id: str,
    ) -> dict:
        backtest = self.rolling_backtest(
            club_id=club_id,
            window_size=20,
        )
        reliability = self.reliability_report(
            report_id=f"auto:{club_id}:{int(time.time())}",
            club_id=club_id,
        )
        reasons = []
        recommended = False

        if backtest["evaluated"] >= 5:
            if backtest["mean_brier_score"] > 0.70:
                recommended = True
                reasons.append(
                    "Brier skoru kabul edilebilir seviyenin üzerinde"
                )
            if backtest["mean_goal_error"] > 1.0:
                recommended = True
                reasons.append(
                    "Ortalama gol hatası yüksek"
                )
            if backtest["result_accuracy"] < 40:
                recommended = True
                reasons.append(
                    "Sonuç doğruluğu düşük"
                )
        if reliability.expected_calibration_error > 0.12:
            recommended = True
            reasons.append(
                "Olasılık kalibrasyon hatası yüksek"
            )
        if not reasons:
            reasons.append(
                "Acil yeniden kalibrasyon ihtiyacı tespit edilmedi"
            )

        return {
            "club_id": club_id,
            "recommended": recommended,
            "reasons": reasons,
            "backtest": backtest,
            "reliability_grade": (
                reliability.reliability_grade
            ),
            "expected_calibration_error": (
                reliability.expected_calibration_error
            ),
        }

    def benchmark_models(
        self,
        *,
        benchmark_id: str,
        club_id: str,
        now: int | None = None,
    ) -> BenchmarkReport:
        rows = []
        for prediction in self.repository.list_predictions(
            club_id
        ):
            evaluations = self.repository.list_evaluations(
                prediction.prediction_id
            )
            if not evaluations:
                continue
            evaluation = evaluations[-1]
            actual = self._result(
                evaluation.actual_home_goals,
                evaluation.actual_away_goals,
            )
            probs = {
                "HOME": prediction.home_win_probability / 100,
                "DRAW": prediction.draw_probability / 100,
                "AWAY": prediction.away_win_probability / 100,
            }
            model_brier = sum(
                (
                    probs[result]
                    - (1.0 if result == actual else 0.0)
                ) ** 2
                for result in ("HOME", "DRAW", "AWAY")
            )
            home_probs = {
                "HOME": 1.0,
                "DRAW": 0.0,
                "AWAY": 0.0,
            }
            home_brier = sum(
                (
                    home_probs[result]
                    - (1.0 if result == actual else 0.0)
                ) ** 2
                for result in ("HOME", "DRAW", "AWAY")
            )
            uniform_brier = sum(
                (
                    1 / 3
                    - (1.0 if result == actual else 0.0)
                ) ** 2
                for result in ("HOME", "DRAW", "AWAY")
            )
            predicted = max(probs, key=probs.get)
            rows.append({
                "model_brier": model_brier,
                "home_brier": home_brier,
                "uniform_brier": uniform_brier,
                "model_correct": predicted == actual,
                "home_correct": actual == "HOME",
            })

        total = len(rows)
        if total == 0:
            raise MatchIntelligenceValidationError(
                "Benchmark için değerlendirilmiş tahmin yok"
            )

        model_brier = sum(
            row["model_brier"] for row in rows
        ) / total
        home_brier = sum(
            row["home_brier"] for row in rows
        ) / total
        uniform_brier = sum(
            row["uniform_brier"] for row in rows
        ) / total
        model_accuracy = sum(
            1 for row in rows if row["model_correct"]
        ) / total * 100
        home_accuracy = sum(
            1 for row in rows if row["home_correct"]
        ) / total * 100
        skill = (
            1.0 - model_brier / uniform_brier
            if uniform_brier > 0
            else 0.0
        )
        verdict = (
            "STRONG"
            if skill >= 0.20 and model_accuracy > home_accuracy
            else "USEFUL"
            if skill > 0
            else "NEEDS_IMPROVEMENT"
        )

        item = BenchmarkReport(
            benchmark_id=benchmark_id,
            club_id=club_id,
            evaluated_predictions=total,
            model_brier_score=round(model_brier, 4),
            home_always_brier_score=round(home_brier, 4),
            uniform_brier_score=round(uniform_brier, 4),
            model_result_accuracy=round(model_accuracy, 2),
            home_always_accuracy=round(home_accuracy, 2),
            model_skill_score=round(skill, 4),
            verdict=verdict,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_benchmark(item)

    def reliability_report(
        self,
        *,
        report_id: str,
        club_id: str,
        now: int | None = None,
    ) -> ReliabilityReport:
        buckets = [
            (0.0, 0.2),
            (0.2, 0.4),
            (0.4, 0.6),
            (0.6, 0.8),
            (0.8, 1.01),
        ]
        observations = {
            index: []
            for index in range(len(buckets))
        }

        for prediction in self.repository.list_predictions(
            club_id
        ):
            evaluations = self.repository.list_evaluations(
                prediction.prediction_id
            )
            if not evaluations:
                continue
            evaluation = evaluations[-1]
            actual = self._result(
                evaluation.actual_home_goals,
                evaluation.actual_away_goals,
            )
            outcome_probs = [
                ("HOME", prediction.home_win_probability / 100),
                ("DRAW", prediction.draw_probability / 100),
                ("AWAY", prediction.away_win_probability / 100),
            ]
            for outcome, probability in outcome_probs:
                for index, (lower, upper) in enumerate(buckets):
                    if lower <= probability < upper:
                        observations[index].append(
                            (
                                probability,
                                1.0 if outcome == actual else 0.0,
                            )
                        )
                        break

        rows = []
        weighted_gap = 0.0
        maximum_gap = 0.0
        total_observations = sum(
            len(items)
            for items in observations.values()
        )
        for index, (lower, upper) in enumerate(buckets):
            items = observations[index]
            if items:
                mean_confidence = sum(
                    item[0] for item in items
                ) / len(items)
                observed = sum(
                    item[1] for item in items
                ) / len(items)
                gap = abs(mean_confidence - observed)
            else:
                mean_confidence = 0.0
                observed = 0.0
                gap = 0.0
            weighted_gap += (
                gap * len(items)
                / max(1, total_observations)
            )
            maximum_gap = max(maximum_gap, gap)
            rows.append({
                "bucket": (
                    f"{int(lower * 100)}-"
                    f"{int(min(1.0, upper) * 100)}"
                ),
                "lower_bound": lower,
                "upper_bound": min(1.0, upper),
                "predictions": len(items),
                "mean_confidence": round(
                    mean_confidence * 100,
                    2,
                ),
                "observed_frequency": round(
                    observed * 100,
                    2,
                ),
                "calibration_gap": round(
                    gap * 100,
                    2,
                ),
            })

        grade = (
            "A"
            if weighted_gap <= 0.05
            else "B"
            if weighted_gap <= 0.10
            else "C"
            if weighted_gap <= 0.18
            else "D"
        )
        item = ReliabilityReport(
            report_id=report_id,
            club_id=club_id,
            buckets=tuple(rows),
            expected_calibration_error=round(
                weighted_gap,
                4,
            ),
            maximum_calibration_error=round(
                maximum_gap,
                4,
            ),
            reliability_grade=grade,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_reliability(item)

    def record_audit_event(
        self,
        *,
        event_id: str,
        prediction_id: str,
        club_id: str,
        event_type: str,
        actor: str,
        details: str,
        now: int | None = None,
    ) -> PredictionAuditEvent:
        if self.repository.get_prediction(prediction_id) is None:
            raise KeyError("Tahmin bulunamadı")
        item = PredictionAuditEvent(
            event_id=event_id,
            prediction_id=prediction_id,
            club_id=club_id,
            event_type=event_type.upper(),
            actor=actor.strip(),
            details=details.strip(),
            created_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_audit_event(item)

    def shareable_report(
        self,
        *,
        prediction_id: str,
        club_id: str,
        data_quality_score: float,
    ) -> dict:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")
        decisions = self.repository.list_decisions(
            prediction_id
        )
        audits = self.repository.list_audit_events(
            prediction_id
        )
        latest_decision = (
            decisions[-1].status
            if decisions
            else "PENDING"
        )
        return {
            "title": (
                f"{prediction.home_team} - "
                f"{prediction.away_team} Maç Analizi"
            ),
            "prediction_id": prediction_id,
            "club_id": club_id,
            "predicted_score": (
                f"{prediction.predicted_home_goals}-"
                f"{prediction.predicted_away_goals}"
            ),
            "expected_goals": {
                "home": prediction.expected_home_goals,
                "away": prediction.expected_away_goals,
            },
            "probabilities": {
                "home": prediction.home_win_probability,
                "draw": prediction.draw_probability,
                "away": prediction.away_win_probability,
            },
            "confidence": prediction.confidence,
            "data_quality_score": data_quality_score,
            "likely_scores": list(
                prediction.likely_scores
            ),
            "factors": list(prediction.factors),
            "risks": list(prediction.risks),
            "approval_status": latest_decision,
            "audit_events": [
                event.__dict__
                for event in audits
            ],
            "disclaimer": (
                "Bu rapor karar desteğidir; kesin sonuç garantisi vermez."
            ),
        }

    def batch_predict_upcoming(
        self,
        *,
        club_id: str,
        club_profile_id: str,
        opponent_profile_id: str,
        limit: int = 10,
        now: int | None = None,
    ) -> tuple[MatchPrediction, ...]:
        matches = [
            item
            for item in self.workspace_service.repository.list_matches(
                club_id
            )
            if item.status == "SCHEDULED"
        ]
        matches.sort(key=lambda item: item.kickoff_at)
        created = []
        current = int(now if now is not None else time.time())
        automatic_impact = self.automatic_unavailable_impact(
            club_id=club_id
        )
        for index, match in enumerate(matches[:limit], start=1):
            prediction_id = (
                f"batch:{club_id}:{match.match_id}:{current}:{index}"
            )
            created.append(
                self.predict(
                    prediction_id=prediction_id,
                    club_id=club_id,
                    match_id=match.match_id,
                    club_profile_id=club_profile_id,
                    opponent_profile_id=opponent_profile_id,
                    unavailable_impact=automatic_impact,
                    now=current,
                )
            )
        return tuple(created)

    def generate_alerts(
        self,
        *,
        club_id: str,
        prediction_id: str,
        data_quality_score: float,
        confidence_threshold: float = 45.0,
        now: int | None = None,
    ) -> tuple[PredictionAlert, ...]:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")

        current = int(now if now is not None else time.time())
        alerts = []
        strongest = max(
            prediction.home_win_probability,
            prediction.draw_probability,
            prediction.away_win_probability,
        )

        def add(severity: str, alert_type: str, message: str):
            item = PredictionAlert(
                alert_id=(
                    f"{prediction_id}:{alert_type}:{len(alerts)+1}"
                ),
                prediction_id=prediction_id,
                club_id=club_id,
                severity=severity,
                alert_type=alert_type,
                message=message,
                acknowledged=False,
                created_at=current,
            )
            self.repository.save_alert(item)
            alerts.append(item)

        if strongest < confidence_threshold:
            add(
                "HIGH",
                "LOW_CONFIDENCE",
                "1X2 olasılıkları birbirine yakın; karar için manuel inceleme gerekli.",
            )
        if data_quality_score < 55:
            add(
                "HIGH",
                "LOW_DATA_QUALITY",
                "Tahmin düşük veri kalitesine dayanıyor.",
            )
        elif data_quality_score < 70:
            add(
                "MEDIUM",
                "MEDIUM_DATA_QUALITY",
                "Veri kapsamı sınırlı; tahmin temkinli yorumlanmalı.",
            )
        if prediction.confidence == "LOW":
            add(
                "MEDIUM",
                "MODEL_CONFIDENCE",
                "Model güven seviyesi LOW.",
            )
        if (
            abs(
                prediction.expected_home_goals
                - prediction.expected_away_goals
            )
            < 0.20
        ):
            add(
                "LOW",
                "BALANCED_MATCH",
                "Beklenen gol dengesi çok yakın.",
            )
        if not alerts:
            add(
                "LOW",
                "READY",
                "Tahmin karar raporu için yeterli görünüyor.",
            )
        return tuple(alerts)

    def review_prediction(
        self,
        *,
        decision_id: str,
        prediction_id: str,
        club_id: str,
        status: str,
        reviewer: str,
        note: str = "",
        now: int | None = None,
    ) -> PredictionDecision:
        allowed = {"PENDING", "APPROVED", "REJECTED", "NEEDS_REVIEW"}
        normalized = status.upper()
        if normalized not in allowed:
            raise MatchIntelligenceValidationError(
                "Geçersiz tahmin karar durumu"
            )
        if self.repository.get_prediction(prediction_id) is None:
            raise KeyError("Tahmin bulunamadı")
        item = PredictionDecision(
            decision_id=decision_id,
            prediction_id=prediction_id,
            club_id=club_id,
            status=normalized,
            reviewer=reviewer.strip(),
            note=note.strip(),
            decided_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_decision(item)

    def decision_report(
        self,
        *,
        report_id: str,
        prediction_id: str,
        club_id: str,
        data_quality_score: float,
        now: int | None = None,
    ) -> MatchDecisionReport:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")

        outcomes = {
            prediction.home_team: prediction.home_win_probability,
            "Beraberlik": prediction.draw_probability,
            prediction.away_team: prediction.away_win_probability,
        }
        recommended = max(outcomes, key=outcomes.get)
        decisions = self.repository.list_decisions(
            prediction_id
        )
        approval_status = (
            decisions[-1].status
            if decisions
            else "PENDING"
        )

        tactical_focus = []
        if prediction.expected_home_goals > prediction.expected_away_goals:
            tactical_focus.append(
                "Hücum üstünlüğünü ilk 30 dakikada skora çevir"
            )
        else:
            tactical_focus.append(
                "Savunma dengesi ve geçiş savunmasına öncelik ver"
            )
        if prediction.draw_probability >= 28:
            tactical_focus.append(
                "Duran top ve maç sonu senaryolarını hazırla"
            )
        if prediction.expected_away_goals >= 1.30:
            tactical_focus.append(
                "Rakibin ceza sahası girişlerini sınırlamaya odaklan"
            )
        if data_quality_score < 70:
            tactical_focus.append(
                "Son kadrolar ve sakatlık bilgileriyle tahmini tekrar çalıştır"
            )

        item = MatchDecisionReport(
            report_id=report_id,
            prediction_id=prediction_id,
            club_id=club_id,
            headline=(
                f"Önerilen sonuç: {recommended} "
                f"(%{outcomes[recommended]:.1f})"
            ),
            recommended_result=recommended,
            predicted_score=(
                f"{prediction.predicted_home_goals}-"
                f"{prediction.predicted_away_goals}"
            ),
            expected_goals=(
                f"{prediction.expected_home_goals}-"
                f"{prediction.expected_away_goals}"
            ),
            confidence=prediction.confidence,
            data_quality_score=data_quality_score,
            key_factors=tuple(prediction.factors[:5]),
            key_risks=tuple(prediction.risks[:5]),
            tactical_focus=tuple(tactical_focus),
            approval_status=approval_status,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_decision_report(item)

    def register_model(
        self,
        *,
        model_id: str,
        club_id: str,
        model_version: str,
        competition: str,
        feature_set: tuple[str, ...],
        training_sample_size: int,
        validation_brier_score: float,
        validation_log_loss: float,
        status: str = "CANDIDATE",
        now: int | None = None,
    ) -> ModelRegistryEntry:
        allowed = {"CANDIDATE", "ACTIVE", "ARCHIVED"}
        normalized_status = status.upper()
        if normalized_status not in allowed:
            raise MatchIntelligenceValidationError(
                "Geçersiz model durumu"
            )
        if training_sample_size < 0:
            raise MatchIntelligenceValidationError(
                "Eğitim örneklem sayısı negatif olamaz"
            )
        current = int(
            now if now is not None else time.time()
        )
        item = ModelRegistryEntry(
            model_id=model_id,
            club_id=club_id,
            model_version=model_version,
            status=normalized_status,
            competition=competition.strip() or "ALL",
            feature_set=tuple(feature_set),
            training_sample_size=training_sample_size,
            validation_brier_score=validation_brier_score,
            validation_log_loss=validation_log_loss,
            promoted_at=(
                current
                if normalized_status == "ACTIVE"
                else 0
            ),
            created_at=current,
        )
        return self.repository.save_model(item)

    def promote_model(
        self,
        *,
        model_id: str,
        now: int | None = None,
    ) -> ModelRegistryEntry:
        model = self.repository.get_model(model_id)
        if model is None:
            raise KeyError("Model bulunamadı")
        current = int(
            now if now is not None else time.time()
        )
        for other in self.repository.list_models(
            model.club_id
        ):
            if (
                other.model_id != model_id
                and other.status == "ACTIVE"
                and other.competition == model.competition
            ):
                self.repository.save_model(
                    ModelRegistryEntry(
                        **{
                            **other.__dict__,
                            "status": "ARCHIVED",
                        }
                    )
                )
        promoted = ModelRegistryEntry(
            **{
                **model.__dict__,
                "status": "ACTIVE",
                "promoted_at": current,
            }
        )
        return self.repository.save_model(promoted)

    def competition_strength(
        self,
        *,
        club_id: str,
        competition: str,
    ) -> dict:
        matches = [
            item
            for item in self.workspace_service.repository.list_matches(
                club_id
            )
            if item.competition.lower()
            == competition.lower()
            and item.status == "COMPLETED"
        ]
        if not matches:
            return {
                "competition": competition,
                "sample_size": 0,
                "goal_environment": 1.0,
                "home_advantage": 1.0,
                "variance_index": 1.0,
            }

        total_goals = [
            (item.goals_for or 0)
            + (item.goals_against or 0)
            for item in matches
        ]
        goal_environment = (
            sum(total_goals) / len(total_goals) / 2.6
        )
        home_matches = [
            item
            for item in matches
            if item.venue == "HOME"
        ]
        home_advantage = (
            (
                sum(
                    (item.goals_for or 0)
                    - (item.goals_against or 0)
                    for item in home_matches
                )
                / max(1, len(home_matches))
            )
            / 2.0
            + 1.0
        )
        mean = sum(total_goals) / len(total_goals)
        variance = (
            sum(
                (value - mean) ** 2
                for value in total_goals
            )
            / len(total_goals)
        )
        variance_index = variance / max(0.5, mean)

        return {
            "competition": competition,
            "sample_size": len(matches),
            "goal_environment": round(
                self._clamp(
                    goal_environment,
                    0.70,
                    1.35,
                ),
                3,
            ),
            "home_advantage": round(
                self._clamp(
                    home_advantage,
                    0.85,
                    1.20,
                ),
                3,
            ),
            "variance_index": round(
                self._clamp(
                    variance_index,
                    0.50,
                    1.80,
                ),
                3,
            ),
        }

    def snapshot_prediction(
        self,
        *,
        snapshot_id: str,
        prediction_id: str,
        model_id: str,
        data_quality_score: float,
        now: int | None = None,
    ) -> PredictionSnapshot:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        model = self.repository.get_model(model_id)
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")
        if model is None:
            raise KeyError("Model bulunamadı")
        item = PredictionSnapshot(
            snapshot_id=snapshot_id,
            prediction_id=prediction_id,
            model_id=model_id,
            home_probability=prediction.home_win_probability,
            draw_probability=prediction.draw_probability,
            away_probability=prediction.away_win_probability,
            expected_home_goals=prediction.expected_home_goals,
            expected_away_goals=prediction.expected_away_goals,
            data_quality_score=data_quality_score,
            created_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_snapshot(item)

    def rolling_backtest(
        self,
        *,
        club_id: str,
        window_size: int = 20,
    ) -> dict:
        if not 5 <= window_size <= 100:
            raise MatchIntelligenceValidationError(
                "Backtest pencere boyutu 5 ile 100 arasında olmalıdır"
            )
        predictions = list(
            self.repository.list_predictions(club_id)
        )
        predictions.sort(
            key=lambda item: item.generated_at
        )
        selected = predictions[-window_size:]

        rows = []
        for prediction in selected:
            evaluations = (
                self.repository.list_evaluations(
                    prediction.prediction_id
                )
            )
            if not evaluations:
                continue
            evaluation = evaluations[-1]
            actual_result = self._result(
                evaluation.actual_home_goals,
                evaluation.actual_away_goals,
            )
            probs = {
                "HOME": (
                    prediction.home_win_probability
                    / 100
                ),
                "DRAW": (
                    prediction.draw_probability
                    / 100
                ),
                "AWAY": (
                    prediction.away_win_probability
                    / 100
                ),
            }
            brier = sum(
                (
                    probs[result]
                    - (
                        1.0
                        if result == actual_result
                        else 0.0
                    )
                ) ** 2
                for result in (
                    "HOME",
                    "DRAW",
                    "AWAY",
                )
            )
            rows.append({
                "prediction_id": prediction.prediction_id,
                "result_correct": evaluation.result_correct,
                "exact_score_correct": evaluation.exact_score_correct,
                "goal_error": evaluation.goal_error,
                "brier_score": brier,
            })

        if not rows:
            return {
                "club_id": club_id,
                "window_size": window_size,
                "evaluated": 0,
                "result_accuracy": 0.0,
                "exact_score_accuracy": 0.0,
                "mean_goal_error": 0.0,
                "mean_brier_score": 0.0,
                "rows": [],
            }

        return {
            "club_id": club_id,
            "window_size": window_size,
            "evaluated": len(rows),
            "result_accuracy": round(
                sum(
                    1
                    for row in rows
                    if row["result_correct"]
                )
                / len(rows)
                * 100,
                2,
            ),
            "exact_score_accuracy": round(
                sum(
                    1
                    for row in rows
                    if row["exact_score_correct"]
                )
                / len(rows)
                * 100,
                2,
            ),
            "mean_goal_error": round(
                sum(row["goal_error"] for row in rows)
                / len(rows),
                3,
            ),
            "mean_brier_score": round(
                sum(row["brier_score"] for row in rows)
                / len(rows),
                4,
            ),
            "rows": rows,
        }

    def drift_report(
        self,
        *,
        drift_id: str,
        club_id: str,
        model_id: str,
        window_size: int = 10,
        now: int | None = None,
    ) -> DriftReport:
        model = self.repository.get_model(model_id)
        if model is None:
            raise KeyError("Model bulunamadı")

        recent = self.rolling_backtest(
            club_id=club_id,
            window_size=window_size,
        )
        baseline = self.rolling_backtest(
            club_id=club_id,
            window_size=min(100, window_size * 2),
        )

        accuracy_change = (
            recent["result_accuracy"]
            - baseline["result_accuracy"]
        )
        brier_change = (
            recent["mean_brier_score"]
            - baseline["mean_brier_score"]
        )
        goal_error_change = (
            recent["mean_goal_error"]
            - baseline["mean_goal_error"]
        )

        snapshots = [
            snapshot
            for prediction in self.repository.list_predictions(
                club_id
            )
            for snapshot in self.repository.list_snapshots(
                prediction.prediction_id
            )
            if snapshot.model_id == model_id
        ]
        probability_shift = 0.0
        if len(snapshots) >= 2:
            first = snapshots[0]
            last = snapshots[-1]
            probability_shift = (
                abs(
                    last.home_probability
                    - first.home_probability
                )
                + abs(
                    last.draw_probability
                    - first.draw_probability
                )
                + abs(
                    last.away_probability
                    - first.away_probability
                )
            ) / 3

        severity_score = (
            max(0.0, -accuracy_change) / 20
            + max(0.0, brier_change) * 2
            + max(0.0, goal_error_change) / 2
            + probability_shift / 30
        )
        drift_level = (
            "HIGH"
            if severity_score >= 1.0
            else "MEDIUM"
            if severity_score >= 0.45
            else "LOW"
        )
        warnings = []
        if accuracy_change <= -10:
            warnings.append(
                "Sonuç doğruluğunda belirgin düşüş"
            )
        if brier_change >= 0.10:
            warnings.append(
                "Olasılık kalibrasyonu kötüleşiyor"
            )
        if goal_error_change >= 0.40:
            warnings.append(
                "Beklenen gol tahmin hatası artıyor"
            )
        if probability_shift >= 12:
            warnings.append(
                "Tahmin olasılıklarında veri dağılımı kayması"
            )
        if not warnings:
            warnings.append(
                "Belirgin model sapması tespit edilmedi"
            )

        item = DriftReport(
            drift_id=drift_id,
            club_id=club_id,
            model_id=model_id,
            window_size=window_size,
            result_accuracy_change=round(
                accuracy_change,
                2,
            ),
            brier_score_change=round(
                brier_change,
                4,
            ),
            mean_goal_error_change=round(
                goal_error_change,
                3,
            ),
            probability_shift=round(
                probability_shift,
                3,
            ),
            drift_level=drift_level,
            warnings=tuple(warnings),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_drift(item)

    def match_context_report(
        self,
        *,
        context_id: str,
        club_id: str,
        match_id: str,
        league_strength: float,
        rest_days: int,
        opponent_rest_days: int,
        travel_km: float,
        temperature_c: float,
        wind_kmh: float,
        precipitation_mm: float,
        referee_card_rate: float,
        now: int | None = None,
    ) -> MatchContextReport:
        if not 0.5 <= league_strength <= 1.5:
            raise MatchIntelligenceValidationError(
                "Lig gücü 0.5 ile 1.5 arasında olmalıdır"
            )
        if rest_days < 0 or opponent_rest_days < 0:
            raise MatchIntelligenceValidationError(
                "Dinlenme günü negatif olamaz"
            )
        if travel_km < 0:
            raise MatchIntelligenceValidationError(
                "Seyahat mesafesi negatif olamaz"
            )

        fatigue_delta = opponent_rest_days - rest_days
        fatigue_modifier = self._clamp(
            fatigue_delta * 0.018,
            -0.12,
            0.12,
        )
        travel_modifier = self._clamp(
            -(travel_km / 3500.0),
            -0.18,
            0.0,
        )

        heat_penalty = (
            -0.05
            if temperature_c >= 32
            else -0.03
            if temperature_c >= 28
            else 0.0
        )
        cold_penalty = (
            -0.03
            if temperature_c <= 2
            else 0.0
        )
        wind_penalty = self._clamp(
            -(max(0.0, wind_kmh - 20.0) / 200.0),
            -0.08,
            0.0,
        )
        rain_penalty = self._clamp(
            -(precipitation_mm / 100.0),
            -0.06,
            0.0,
        )
        weather_home = heat_penalty + cold_penalty + wind_penalty + rain_penalty
        weather_away = weather_home * 1.08
        referee_variance = self._clamp(
            (referee_card_rate - 4.0) / 25.0,
            -0.08,
            0.12,
        )

        warnings = []
        if rest_days <= 3:
            warnings.append(
                "Kulüp için kısa dinlenme süresi"
            )
        if travel_km >= 1200:
            warnings.append(
                "Yüksek seyahat yükü"
            )
        if temperature_c >= 30:
            warnings.append(
                "Yüksek sıcaklık performansı etkileyebilir"
            )
        if wind_kmh >= 30:
            warnings.append(
                "Şiddetli rüzgar pas ve şut kalitesini etkileyebilir"
            )
        if referee_card_rate >= 5.5:
            warnings.append(
                "Hakem kart ortalaması yüksek; kırmızı kart varyansı artabilir"
            )
        if not warnings:
            warnings.append(
                "Maç bağlamında belirgin dış risk yok"
            )

        item = MatchContextReport(
            context_id=context_id,
            club_id=club_id,
            match_id=match_id,
            league_strength=league_strength,
            rest_days=rest_days,
            opponent_rest_days=opponent_rest_days,
            travel_km=travel_km,
            temperature_c=temperature_c,
            wind_kmh=wind_kmh,
            precipitation_mm=precipitation_mm,
            referee_card_rate=referee_card_rate,
            fatigue_modifier=round(fatigue_modifier, 3),
            travel_modifier=round(travel_modifier, 3),
            weather_home_modifier=round(weather_home, 3),
            weather_away_modifier=round(weather_away, 3),
            referee_variance_modifier=round(
                referee_variance,
                3,
            ),
            warnings=tuple(warnings),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_match_context(item)

    def live_update(
        self,
        *,
        state_id: str,
        prediction_id: str,
        minute: int,
        home_goals: int,
        away_goals: int,
        home_red_cards: int = 0,
        away_red_cards: int = 0,
        home_xg_live: float = 0.0,
        away_xg_live: float = 0.0,
        now: int | None = None,
    ) -> LiveMatchState:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")
        if not 0 <= minute <= 130:
            raise MatchIntelligenceValidationError(
                "Dakika 0 ile 130 arasında olmalıdır"
            )
        if min(
            home_goals,
            away_goals,
            home_red_cards,
            away_red_cards,
        ) < 0:
            raise MatchIntelligenceValidationError(
                "Canlı maç değerleri negatif olamaz"
            )

        remaining = self._clamp(
            (90 - minute) / 90.0,
            0.0,
            1.0,
        )
        remaining_home_xg = (
            prediction.expected_home_goals
            * remaining
            * (0.78 ** home_red_cards)
            * (1.12 ** away_red_cards)
        )
        remaining_away_xg = (
            prediction.expected_away_goals
            * remaining
            * (0.78 ** away_red_cards)
            * (1.12 ** home_red_cards)
        )
        if home_xg_live > 0:
            remaining_home_xg *= self._clamp(
                0.75 + home_xg_live / max(
                    0.2,
                    prediction.expected_home_goals,
                ) * 0.25,
                0.70,
                1.35,
            )
        if away_xg_live > 0:
            remaining_away_xg *= self._clamp(
                0.75 + away_xg_live / max(
                    0.2,
                    prediction.expected_away_goals,
                ) * 0.25,
                0.70,
                1.35,
            )

        home_win = draw = away_win = 0.0
        for additional_home in range(0, 7):
            for additional_away in range(0, 7):
                probability = (
                    self._poisson(
                        additional_home,
                        remaining_home_xg,
                    )
                    * self._poisson(
                        additional_away,
                        remaining_away_xg,
                    )
                )
                final_home = home_goals + additional_home
                final_away = away_goals + additional_away
                if final_home > final_away:
                    home_win += probability
                elif final_home == final_away:
                    draw += probability
                else:
                    away_win += probability
        total = home_win + draw + away_win
        home_win /= total
        draw /= total
        away_win /= total

        next_goal_total = (
            remaining_home_xg + remaining_away_xg
        )
        next_home = (
            remaining_home_xg / next_goal_total
            if next_goal_total > 0
            else 0.5
        )
        next_away = 1.0 - next_home

        item = LiveMatchState(
            state_id=state_id,
            prediction_id=prediction_id,
            minute=minute,
            home_goals=home_goals,
            away_goals=away_goals,
            home_red_cards=home_red_cards,
            away_red_cards=away_red_cards,
            home_xg_live=home_xg_live,
            away_xg_live=away_xg_live,
            home_win_probability=round(
                home_win * 100,
                2,
            ),
            draw_probability=round(draw * 100, 2),
            away_win_probability=round(
                away_win * 100,
                2,
            ),
            next_goal_home_probability=round(
                next_home * 100,
                2,
            ),
            next_goal_away_probability=round(
                next_away * 100,
                2,
            ),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_live_state(item)

    def explain_prediction(
        self,
        *,
        report_id: str,
        prediction_id: str,
        lineup_report_id: str | None = None,
        tactical_matchup_id: str | None = None,
        context_id: str | None = None,
        now: int | None = None,
    ) -> ExplainabilityReport:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")

        contributions = [
            {
                "factor": "home_advantage",
                "impact": 0.14,
                "direction": "HOME",
            },
            {
                "factor": "expected_goal_balance",
                "impact": round(
                    prediction.expected_home_goals
                    - prediction.expected_away_goals,
                    3,
                ),
                "direction": (
                    "HOME"
                    if prediction.expected_home_goals
                    >= prediction.expected_away_goals
                    else "AWAY"
                ),
            },
        ]

        if lineup_report_id:
            lineup = self.repository.get_lineup_report(
                lineup_report_id
            )
            if lineup is None:
                raise KeyError("Kadro etki raporu bulunamadı")
            contributions.extend([
                {
                    "factor": "lineup_attack",
                    "impact": round(
                        lineup.attack_modifier - 1.0,
                        3,
                    ),
                    "direction": "HOME",
                },
                {
                    "factor": "lineup_availability",
                    "impact": round(
                        -lineup.availability_penalty,
                        3,
                    ),
                    "direction": "AWAY",
                },
            ])

        if tactical_matchup_id:
            tactical = self.repository.get_tactical_matchup(
                tactical_matchup_id
            )
            if tactical is None:
                raise KeyError("Taktik eşleşme bulunamadı")
            contributions.append({
                "factor": "tactical_matchup",
                "impact": tactical.net_home_xg_modifier,
                "direction": (
                    "HOME"
                    if tactical.net_home_xg_modifier >= 0
                    else "AWAY"
                ),
            })

        if context_id:
            context = self.repository.get_match_context(
                context_id
            )
            if context is None:
                raise KeyError("Maç bağlam raporu bulunamadı")
            contributions.extend([
                {
                    "factor": "fatigue",
                    "impact": context.fatigue_modifier,
                    "direction": (
                        "HOME"
                        if context.fatigue_modifier >= 0
                        else "AWAY"
                    ),
                },
                {
                    "factor": "travel",
                    "impact": context.travel_modifier,
                    "direction": "AWAY",
                },
                {
                    "factor": "weather",
                    "impact": context.weather_home_modifier,
                    "direction": (
                        "HOME"
                        if context.weather_home_modifier >= 0
                        else "AWAY"
                    ),
                },
            ])

        positive = max(
            contributions,
            key=lambda item: item["impact"],
        )
        negative = min(
            contributions,
            key=lambda item: item["impact"],
        )
        sorted_contributions = tuple(
            sorted(
                contributions,
                key=lambda item: abs(item["impact"]),
                reverse=True,
            )
        )
        narrative = (
            f"Tahmini en fazla {positive['factor']} "
            f"olumlu etkiliyor; en büyük negatif sinyal "
            f"{negative['factor']}. Beklenen gol dengesi "
            f"{prediction.expected_home_goals}-"
            f"{prediction.expected_away_goals}."
        )

        item = ExplainabilityReport(
            report_id=report_id,
            prediction_id=prediction_id,
            contributions=sorted_contributions,
            strongest_positive_factor=positive["factor"],
            strongest_negative_factor=negative["factor"],
            narrative=narrative,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_explainability(item)

    def lineup_impact_report(
        self,
        *,
        report_id: str,
        club_id: str,
        match_id: str,
        selected_player_ids: tuple[str, ...],
        now: int | None = None,
    ) -> LineupImpactReport:
        players = {
            item.player_id: item
            for item in self.workspace_service
            .repository.list_players(club_id)
        }
        if not players:
            raise MatchIntelligenceValidationError(
                "Kadroda oyuncu bulunamadı"
            )
        selected = [
            players[player_id]
            for player_id in selected_player_ids
            if player_id in players
        ]
        if len(selected) < 7:
            raise MatchIntelligenceValidationError(
                "En az 7 oyuncu seçilmelidir"
            )

        position_weights = {
            "GK": 0.90,
            "CB": 0.95,
            "LB": 0.92,
            "RB": 0.92,
            "DM": 0.96,
            "CM": 1.00,
            "AM": 1.04,
            "LW": 1.08,
            "RW": 1.08,
            "ST": 1.12,
        }
        availability_penalties = {
            "AVAILABLE": 0.0,
            "DOUBTFUL": 0.08,
            "REST": 0.04,
            "INJURED": 0.30,
            "SUSPENDED": 0.35,
        }

        raw_strengths = []
        attack_values = []
        defence_values = []
        warnings = []
        unavailable_penalty = 0.0

        for player in selected:
            base = (
                0.55
                + min(player.market_value, 50.0) / 100.0
                + max(0, 30 - player.age) / 200.0
            )
            weighted = base * position_weights.get(
                player.position,
                1.0,
            )
            penalty = availability_penalties.get(
                player.availability,
                0.05,
            )
            unavailable_penalty += penalty
            weighted *= 1.0 - penalty
            raw_strengths.append(weighted)
            if player.position in {
                "AM",
                "LW",
                "RW",
                "ST",
                "CM",
            }:
                attack_values.append(weighted)
            if player.position in {
                "GK",
                "CB",
                "LB",
                "RB",
                "DM",
            }:
                defence_values.append(weighted)

            if player.availability in {
                "INJURED",
                "SUSPENDED",
            }:
                warnings.append(
                    f"{player.name} uygun değil"
                )

        starter_strength = sum(raw_strengths) / len(
            raw_strengths
        )
        bench = [
            player
            for player_id, player in players.items()
            if player_id not in selected_player_ids
        ]
        bench_strength = (
            sum(
                0.55
                + min(player.market_value, 50.0) / 100.0
                for player in bench
            )
            / len(bench)
            if bench
            else 0.0
        )
        attack_strength = (
            sum(attack_values) / len(attack_values)
            if attack_values
            else starter_strength
        )
        defence_strength = (
            sum(defence_values) / len(defence_values)
            if defence_values
            else starter_strength
        )
        unique_positions = len(
            {player.position for player in selected}
        )
        cohesion = self._clamp(
            0.55
            + unique_positions / 20.0
            + min(len(selected), 11) / 40.0,
            0.0,
            1.0,
        )

        if len(selected) < 11:
            warnings.append(
                "İlk 11 eksik; rapor kısmi kadroya göre üretildi"
            )
        if not warnings:
            warnings.append("Kadro uygunluk kontrolü geçti")

        item = LineupImpactReport(
            report_id=report_id,
            club_id=club_id,
            match_id=match_id,
            selected_player_ids=tuple(selected_player_ids),
            starter_strength=round(starter_strength, 3),
            bench_strength=round(bench_strength, 3),
            attack_modifier=round(
                self._clamp(
                    0.85 + attack_strength * 0.20,
                    0.80,
                    1.20,
                ),
                3,
            ),
            defence_modifier=round(
                self._clamp(
                    1.15 - defence_strength * 0.18,
                    0.78,
                    1.18,
                ),
                3,
            ),
            availability_penalty=round(
                unavailable_penalty / len(selected),
                3,
            ),
            cohesion_score=round(cohesion * 100, 2),
            warnings=tuple(warnings),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_lineup_report(item)

    def tactical_matchup(
        self,
        *,
        matchup_id: str,
        club_id: str,
        match_id: str,
        own_style: str,
        opponent_style: str,
        now: int | None = None,
    ) -> TacticalMatchup:
        styles = {
            "POSSESSION",
            "HIGH_PRESS",
            "LOW_BLOCK",
            "DIRECT",
            "TRANSITION",
            "BALANCED",
        }
        own = own_style.upper()
        opponent = opponent_style.upper()
        if own not in styles or opponent not in styles:
            raise MatchIntelligenceValidationError(
                "Desteklenmeyen taktik stil"
            )

        matrix = {
            ("POSSESSION", "LOW_BLOCK"): (0.05, -0.02, -0.01, 0.02),
            ("POSSESSION", "HIGH_PRESS"): (-0.03, 0.04, -0.04, 0.00),
            ("HIGH_PRESS", "POSSESSION"): (0.03, 0.05, 0.06, 0.00),
            ("HIGH_PRESS", "DIRECT"): (-0.02, -0.03, 0.03, 0.00),
            ("LOW_BLOCK", "POSSESSION"): (-0.04, 0.03, -0.03, 0.04),
            ("DIRECT", "HIGH_PRESS"): (0.01, 0.05, -0.02, 0.01),
            ("TRANSITION", "POSSESSION"): (-0.01, 0.08, 0.01, 0.00),
            ("BALANCED", "BALANCED"): (0.00, 0.00, 0.00, 0.00),
        }
        possession, transition, pressing, set_piece = matrix.get(
            (own, opponent),
            (0.0, 0.0, 0.0, 0.0),
        )
        net_home = (
            possession * 0.35
            + transition * 0.35
            + pressing * 0.20
            + set_piece * 0.10
        )
        net_away = -net_home * 0.75

        notes = [
            f"Bizim stil: {own}",
            f"Rakip stil: {opponent}",
        ]
        if transition >= 0.05:
            notes.append(
                "Geçiş hücumlarında avantaj bekleniyor"
            )
        if pressing <= -0.03:
            notes.append(
                "Rakip baskısı altında top kaybı riski"
            )
        if set_piece >= 0.03:
            notes.append(
                "Duran toplar önemli fırsat olabilir"
            )
        if len(notes) == 2:
            notes.append(
                "Belirgin taktik eşleşme avantajı yok"
            )

        item = TacticalMatchup(
            matchup_id=matchup_id,
            club_id=club_id,
            match_id=match_id,
            own_style=own,
            opponent_style=opponent,
            possession_modifier=possession,
            transition_modifier=transition,
            pressing_modifier=pressing,
            set_piece_modifier=set_piece,
            net_home_xg_modifier=round(net_home, 3),
            net_away_xg_modifier=round(net_away, 3),
            notes=tuple(notes),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_tactical_matchup(item)

    def monte_carlo_simulation(
        self,
        *,
        simulation_id: str,
        prediction_id: str,
        iterations: int = 10000,
        lineup_report_id: str | None = None,
        tactical_matchup_id: str | None = None,
        context_id: str | None = None,
        now: int | None = None,
    ) -> MonteCarloSimulation:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")
        if not 1000 <= iterations <= 100000:
            raise MatchIntelligenceValidationError(
                "Simülasyon iterasyonu 1000 ile 100000 arasında olmalıdır"
            )

        home_xg = prediction.expected_home_goals
        away_xg = prediction.expected_away_goals

        if lineup_report_id:
            lineup = self.repository.get_lineup_report(
                lineup_report_id
            )
            if lineup is None:
                raise KeyError("Kadro etki raporu bulunamadı")
            home_xg *= lineup.attack_modifier
            away_xg *= lineup.defence_modifier

        if tactical_matchup_id:
            tactical = self.repository.get_tactical_matchup(
                tactical_matchup_id
            )
            if tactical is None:
                raise KeyError("Taktik eşleşme bulunamadı")
            home_xg *= 1.0 + tactical.net_home_xg_modifier
            away_xg *= 1.0 + tactical.net_away_xg_modifier

        if context_id:
            context = self.repository.get_match_context(
                context_id
            )
            if context is None:
                raise KeyError("Maç bağlam raporu bulunamadı")
            home_xg *= (
                context.league_strength
                * (1.0 + context.fatigue_modifier)
                * (1.0 + context.weather_home_modifier)
            )
            away_xg *= (
                context.league_strength
                * (1.0 - context.fatigue_modifier)
                * (1.0 + context.travel_modifier)
                * (1.0 + context.weather_away_modifier)
            )

        home_xg = self._clamp(home_xg, 0.10, 4.50)
        away_xg = self._clamp(away_xg, 0.10, 4.50)

        # Deterministic pseudo Monte Carlo based on inverse CDF traversal.
        home_wins = draws = away_wins = 0
        both_score = over_25 = 0
        first_home = first_draw = first_away = 0
        total_home = total_away = 0
        score_counts: dict[tuple[int, int], int] = {}

        for index in range(iterations):
            u_home = (
                ((index * 7919 + 104729) % 1_000_003)
                / 1_000_003
            )
            u_away = (
                ((index * 1543 + 32452843) % 1_000_033)
                / 1_000_033
            )
            home_goals = self._poisson_quantile(
                u_home,
                home_xg,
            )
            away_goals = self._poisson_quantile(
                u_away,
                away_xg,
            )
            total_home += home_goals
            total_away += away_goals
            score_counts[(home_goals, away_goals)] = (
                score_counts.get(
                    (home_goals, away_goals),
                    0,
                )
                + 1
            )
            if home_goals > away_goals:
                home_wins += 1
            elif home_goals == away_goals:
                draws += 1
            else:
                away_wins += 1
            if home_goals > 0 and away_goals > 0:
                both_score += 1
            if home_goals + away_goals >= 3:
                over_25 += 1

            first_home_goals = self._poisson_quantile(
                u_home,
                home_xg * 0.45,
            )
            first_away_goals = self._poisson_quantile(
                u_away,
                away_xg * 0.45,
            )
            if first_home_goals > first_away_goals:
                first_home += 1
            elif first_home_goals == first_away_goals:
                first_draw += 1
            else:
                first_away += 1

        distribution = tuple(
            {
                "score": f"{score[0]}-{score[1]}",
                "probability": round(
                    count / iterations * 100,
                    2,
                ),
            }
            for score, count in sorted(
                score_counts.items(),
                key=lambda item: item[1],
                reverse=True,
            )[:10]
        )

        item = MonteCarloSimulation(
            simulation_id=simulation_id,
            prediction_id=prediction_id,
            iterations=iterations,
            home_win_probability=round(
                home_wins / iterations * 100,
                2,
            ),
            draw_probability=round(
                draws / iterations * 100,
                2,
            ),
            away_win_probability=round(
                away_wins / iterations * 100,
                2,
            ),
            both_teams_score_probability=round(
                both_score / iterations * 100,
                2,
            ),
            over_2_5_probability=round(
                over_25 / iterations * 100,
                2,
            ),
            under_2_5_probability=round(
                (iterations - over_25) / iterations * 100,
                2,
            ),
            first_half_home_probability=round(
                first_home / iterations * 100,
                2,
            ),
            first_half_draw_probability=round(
                first_draw / iterations * 100,
                2,
            ),
            first_half_away_probability=round(
                first_away / iterations * 100,
                2,
            ),
            average_home_goals=round(
                total_home / iterations,
                3,
            ),
            average_away_goals=round(
                total_away / iterations,
                3,
            ),
            score_distribution=distribution,
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_simulation(item)

    def automatic_unavailable_impact(
        self,
        *,
        club_id: str,
    ) -> float:
        players = self.workspace_service.repository.list_players(
            club_id
        )
        if not players:
            return 0.0

        weights = {
            "AVAILABLE": 0.0,
            "DOUBTFUL": 0.03,
            "REST": 0.02,
            "INJURED": 0.08,
            "SUSPENDED": 0.07,
        }
        weighted = sum(
            weights.get(
                player.availability,
                0.02,
            )
            for player in players
        )
        impact = weighted / max(1, len(players)) * 4.0
        return round(self._clamp(impact, 0.0, 0.50), 3)

    def data_quality_report(
        self,
        *,
        report_id: str,
        club_id: str,
        club_profile_id: str,
        opponent_profile_id: str,
        now: int | None = None,
    ) -> DataQualityReport:
        club = self.repository.get_profile(club_profile_id)
        opponent = self.repository.get_profile(
            opponent_profile_id
        )
        if club is None or opponent is None:
            raise KeyError("Takım güç profili bulunamadı")

        club_sample = self._clamp(
            club.sample_size / 15.0,
            0.0,
            1.0,
        )
        opponent_sample = self._clamp(
            opponent.sample_size / 15.0,
            0.0,
            1.0,
        )
        xg_coverage = (
            (
                (1.0 if club.xg_for_average > 0 else 0.0)
                + (1.0 if club.xg_against_average > 0 else 0.0)
                + (1.0 if opponent.xg_for_average > 0 else 0.0)
                + (1.0 if opponent.xg_against_average > 0 else 0.0)
            )
            / 4.0
        )

        players = self.workspace_service.repository.list_players(
            club_id
        )
        availability_coverage = (
            0.0
            if not players
            else sum(
                1
                for player in players
                if bool(player.availability)
            )
            / len(players)
        )

        latest_profile_update = min(
            club.updated_at,
            opponent.updated_at,
        )
        age_seconds = max(
            0,
            int(now if now is not None else time.time())
            - latest_profile_update,
        )
        recency = self._clamp(
            1.0 - age_seconds / (60 * 60 * 24 * 30),
            0.0,
            1.0,
        )

        overall = (
            club_sample * 0.22
            + opponent_sample * 0.22
            + xg_coverage * 0.24
            + availability_coverage * 0.17
            + recency * 0.15
        )
        grade = (
            "A"
            if overall >= 0.85
            else "B"
            if overall >= 0.70
            else "C"
            if overall >= 0.55
            else "D"
        )

        warnings = []
        if club.sample_size < 5:
            warnings.append("Kulüp maç örneklemi düşük")
        if opponent.sample_size < 5:
            warnings.append("Rakip maç örneklemi düşük")
        if xg_coverage < 1.0:
            warnings.append("xG verisi eksik veya kısmi")
        if availability_coverage < 0.80:
            warnings.append("Oyuncu uygunluk verisi eksik")
        if recency < 0.50:
            warnings.append("Takım profilleri güncel değil")
        if not warnings:
            warnings.append("Veri kapsamı yeterli")

        item = DataQualityReport(
            report_id=report_id,
            club_id=club_id,
            club_profile_id=club_profile_id,
            opponent_profile_id=opponent_profile_id,
            club_sample_score=round(club_sample * 100, 2),
            opponent_sample_score=round(
                opponent_sample * 100,
                2,
            ),
            xg_coverage_score=round(xg_coverage * 100, 2),
            availability_coverage_score=round(
                availability_coverage * 100,
                2,
            ),
            recency_score=round(recency * 100, 2),
            overall_score=round(overall * 100, 2),
            grade=grade,
            warnings=tuple(warnings),
            generated_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_data_quality(item)

    def create_ensemble(
        self,
        *,
        ensemble_id: str,
        prediction_id: str,
        data_quality_report_id: str,
        now: int | None = None,
    ) -> EnsemblePrediction:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        quality = self.repository.get_data_quality(
            data_quality_report_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")
        if quality is None:
            raise KeyError("Veri kalite raporu bulunamadı")

        poisson = (
            prediction.home_win_probability / 100,
            prediction.draw_probability / 100,
            prediction.away_win_probability / 100,
        )
        home_profile = self.repository.get_profile(
            quality.club_profile_id
        )
        opponent = self.repository.get_profile(
            quality.opponent_profile_id
        )
        if home_profile is None or opponent is None:
            raise KeyError("Takım güç profili bulunamadı")

        elo_home = 1.0 / (
            1.0
            + 10 ** (
                (
                    opponent.elo_rating
                    - (home_profile.elo_rating + 65)
                )
                / 400
            )
        )
        elo_draw = self._clamp(
            0.29 - abs(elo_home - 0.5) * 0.18,
            0.16,
            0.30,
        )
        elo_away = 1.0 - elo_home
        elo_home_adjusted = elo_home * (1.0 - elo_draw)
        elo_away_adjusted = elo_away * (1.0 - elo_draw)
        elo_probs = (
            elo_home_adjusted,
            elo_draw,
            elo_away_adjusted,
        )

        quality_factor = quality.overall_score / 100
        poisson_weight = 0.55 + quality_factor * 0.20
        elo_weight = 1.0 - poisson_weight

        blended = tuple(
            poisson[index] * poisson_weight
            + elo_probs[index] * elo_weight
            for index in range(3)
        )
        total = sum(blended)
        blended = tuple(value / total for value in blended)

        uncertainty = (
            0.04
            + (1.0 - quality_factor) * 0.12
        )
        intervals = tuple(
            (
                round(
                    max(0.0, probability - uncertainty)
                    * 100,
                    2,
                ),
                round(
                    min(1.0, probability + uncertainty)
                    * 100,
                    2,
                ),
            )
            for probability in blended
        )

        item = EnsemblePrediction(
            ensemble_id=ensemble_id,
            prediction_id=prediction_id,
            poisson_home_probability=round(
                poisson[0] * 100,
                2,
            ),
            poisson_draw_probability=round(
                poisson[1] * 100,
                2,
            ),
            poisson_away_probability=round(
                poisson[2] * 100,
                2,
            ),
            elo_home_probability=round(
                elo_probs[0] * 100,
                2,
            ),
            elo_draw_probability=round(
                elo_probs[1] * 100,
                2,
            ),
            elo_away_probability=round(
                elo_probs[2] * 100,
                2,
            ),
            blended_home_probability=round(
                blended[0] * 100,
                2,
            ),
            blended_draw_probability=round(
                blended[1] * 100,
                2,
            ),
            blended_away_probability=round(
                blended[2] * 100,
                2,
            ),
            home_probability_interval=intervals[0],
            draw_probability_interval=intervals[1],
            away_probability_interval=intervals[2],
            data_quality_score=quality.overall_score,
            created_at=int(
                now if now is not None else time.time()
            ),
        )
        return self.repository.save_ensemble(item)

    def analysis_brief(
        self,
        *,
        prediction_id: str,
        ensemble_id: str | None = None,
    ) -> dict:
        prediction = self.repository.get_prediction(
            prediction_id
        )
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")

        ensemble = None
        if ensemble_id is not None:
            ensembles = self.repository.list_ensembles(
                prediction_id
            )
            ensemble = next(
                (
                    item
                    for item in ensembles
                    if item.ensemble_id == ensemble_id
                ),
                None,
            )

        probabilities = (
            {
                "home": ensemble.blended_home_probability,
                "draw": ensemble.blended_draw_probability,
                "away": ensemble.blended_away_probability,
            }
            if ensemble is not None
            else {
                "home": prediction.home_win_probability,
                "draw": prediction.draw_probability,
                "away": prediction.away_win_probability,
            }
        )
        strongest = max(
            probabilities,
            key=probabilities.get,
        )
        labels = {
            "home": prediction.home_team,
            "draw": "Beraberlik",
            "away": prediction.away_team,
        }
        return {
            "prediction_id": prediction_id,
            "headline": (
                f"En güçlü sonuç: {labels[strongest]} "
                f"(%{probabilities[strongest]:.1f})"
            ),
            "predicted_score": (
                f"{prediction.predicted_home_goals}-"
                f"{prediction.predicted_away_goals}"
            ),
            "expected_goals": (
                f"{prediction.expected_home_goals}-"
                f"{prediction.expected_away_goals}"
            ),
            "confidence": prediction.confidence,
            "factors": list(prediction.factors),
            "risks": list(prediction.risks),
            "likely_scores": list(
                prediction.likely_scores
            ),
            "ensemble_used": ensemble is not None,
        }

    def create_scenarios(
        self,
        *,
        prediction_id: str,
        labels: tuple[str, ...] = (
            "FULL_SQUAD",
            "ONE_KEY_PLAYER_OUT",
            "OPPONENT_KEY_PLAYER_OUT",
        ),
        now: int | None = None,
    ) -> tuple[ScenarioPrediction, ...]:
        prediction = self.repository.get_prediction(prediction_id)
        if prediction is None:
            raise KeyError("Tahmin bulunamadı")

        scenarios = {
            "FULL_SQUAD": (0.0, 0.0),
            "ONE_KEY_PLAYER_OUT": (0.15, 0.0),
            "OPPONENT_KEY_PLAYER_OUT": (0.0, 0.15),
            "MULTIPLE_ABSENCES": (0.30, 0.0),
        }
        created = []
        current = int(now if now is not None else time.time())
        for index, label in enumerate(labels, start=1):
            if label not in scenarios:
                raise MatchIntelligenceValidationError(
                    f"Desteklenmeyen senaryo: {label}"
                )
            own_impact, opp_impact = scenarios[label]
            home_xg = self._clamp(
                prediction.expected_home_goals
                * (1.0 - own_impact)
                * (1.0 + opp_impact * 0.30),
                0.10,
                4.50,
            )
            away_xg = self._clamp(
                prediction.expected_away_goals
                * (1.0 - opp_impact)
                * (1.0 + own_impact * 0.30),
                0.10,
                4.50,
            )
            home, draw, away = self._outcome_probabilities(
                home_xg,
                away_xg,
            )
            item = ScenarioPrediction(
                scenario_id=f"{prediction_id}:scenario:{index}",
                prediction_id=prediction_id,
                label=label,
                unavailable_impact=own_impact,
                opponent_unavailable_impact=opp_impact,
                expected_home_goals=round(home_xg, 2),
                expected_away_goals=round(away_xg, 2),
                home_win_probability=round(home * 100, 2),
                draw_probability=round(draw * 100, 2),
                away_win_probability=round(away * 100, 2),
                created_at=current,
            )
            self.repository.save_scenario(item)
            created.append(item)
        return tuple(created)

    def calibrate(
        self,
        *,
        calibration_id: str,
        club_id: str,
        now: int | None = None,
    ) -> ModelCalibration:
        predictions = self.repository.list_predictions(club_id)
        evaluated = []
        for prediction in predictions:
            evaluations = self.repository.list_evaluations(
                prediction.prediction_id
            )
            if evaluations:
                evaluated.append((prediction, evaluations[-1]))

        if not evaluated:
            raise MatchIntelligenceValidationError(
                "Kalibrasyon için değerlendirilmiş tahmin yok"
            )

        brier_values = []
        log_losses = []
        for prediction, evaluation in evaluated:
            actual = self._result(
                evaluation.actual_home_goals,
                evaluation.actual_away_goals,
            )
            probs = {
                "HOME": prediction.home_win_probability / 100,
                "DRAW": prediction.draw_probability / 100,
                "AWAY": prediction.away_win_probability / 100,
            }
            brier_values.append(
                sum(
                    (
                        probs[result]
                        - (1.0 if result == actual else 0.0)
                    ) ** 2
                    for result in ("HOME", "DRAW", "AWAY")
                )
            )
            probability = max(1e-9, probs[actual])
            log_losses.append(-math.log(probability))

        brier = sum(brier_values) / len(brier_values)
        log_loss = sum(log_losses) / len(log_losses)

        # Small, conservative weight adjustment based on calibration quality.
        elo_weight = 0.20 if brier <= 0.65 else 0.15
        form_weight = 0.25 if log_loss <= 1.10 else 0.20
        xg_weight = 0.35 if brier <= 0.60 else 0.30
        availability_weight = round(
            1.0 - elo_weight - form_weight - xg_weight,
            2,
        )

        item = ModelCalibration(
            calibration_id=calibration_id,
            club_id=club_id,
            model_version="build-006",
            elo_weight=elo_weight,
            form_weight=form_weight,
            xg_weight=xg_weight,
            availability_weight=availability_weight,
            brier_score=round(brier, 4),
            log_loss=round(log_loss, 4),
            sample_size=len(evaluated),
            created_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_calibration(item)

    def backtest_report(
        self,
        *,
        club_id: str,
    ) -> dict:
        accuracy = self.accuracy_report(club_id=club_id)
        calibrations = self.repository.list_calibrations(club_id)
        latest = calibrations[0] if calibrations else None
        return {
            **accuracy,
            "latest_calibration": (
                latest.__dict__
                if latest is not None
                else None
            ),
            "model_version": "build-006",
        }

    def _expected_goals(
        self,
        *,
        attack: float,
        elo: float,
        opponent_elo: float,
        xg_for: float,
        xg_against: float,
        opponent_defence: float,
        form: float,
        venue_rating: float,
        unavailable: float,
        opponent_unavailable: float,
        home_advantage: float,
    ) -> float:
        base = 1.28
        form_factor = 0.82 + form * 0.36
        venue_factor = 0.86 + venue_rating * 0.28
        availability_factor = 1.0 - unavailable
        opponent_weakness = 0.90 + opponent_defence * 0.22
        opponent_missing = 1.0 + opponent_unavailable * 0.35
        elo_factor = self._clamp(
            1.0 + (elo - opponent_elo) / 1200.0,
            0.75,
            1.25,
        )
        xg_signal = (
            1.0
            if xg_for <= 0 and xg_against <= 0
            else self._clamp(
                ((max(0.1, xg_for) + max(0.1, xg_against)) / 2) / 1.25,
                0.70,
                1.35,
            )
        )
        value = (
            base
            * attack
            * elo_factor
            * xg_signal
            * opponent_weakness
            * form_factor
            * venue_factor
            * availability_factor
            * opponent_missing
            * home_advantage
        )
        return self._clamp(value, 0.15, 4.25)


    def _poisson_quantile(
        self,
        probability: float,
        expected: float,
    ) -> int:
        cumulative = 0.0
        for goals in range(0, 11):
            cumulative += self._poisson(
                goals,
                expected,
            )
            if probability <= cumulative:
                return goals
        return 10

    def _poisson(self, goals: int, expected: float) -> float:
        return (
            math.exp(-expected)
            * expected**goals
            / math.factorial(goals)
        )


    def _outcome_probabilities(
        self,
        home_xg: float,
        away_xg: float,
    ) -> tuple[float, float, float]:
        home = draw = away = 0.0
        for home_goals in range(0, 8):
            for away_goals in range(0, 8):
                probability = (
                    self._poisson(home_goals, home_xg)
                    * self._poisson(away_goals, away_xg)
                )
                if home_goals > away_goals:
                    home += probability
                elif home_goals == away_goals:
                    draw += probability
                else:
                    away += probability
        total = home + draw + away
        return home / total, draw / total, away / total

    def _derive_elo(self, matches) -> float:
        rating = 1500.0
        for match in sorted(matches, key=lambda item: item.kickoff_at):
            actual = (
                1.0
                if (match.goals_for or 0) > (match.goals_against or 0)
                else 0.5
                if match.goals_for == match.goals_against
                else 0.0
            )
            expected = 0.5
            goal_difference = abs(
                (match.goals_for or 0)
                - (match.goals_against or 0)
            )
            multiplier = 1.0 + min(goal_difference, 3) * 0.15
            rating += 24 * multiplier * (actual - expected)
        return rating

    def _result_rating(self, matches) -> float:
        if not matches:
            return 0.50
        points = sum(
            3
            if (item.goals_for or 0) > (item.goals_against or 0)
            else 1
            if item.goals_for == item.goals_against
            else 0
            for item in matches
        )
        return points / (len(matches) * 3)

    def _explain(
        self,
        *,
        match,
        club_profile,
        opponent,
        unavailable_impact,
        opponent_unavailable_impact,
        home_xg,
        away_xg,
    ) -> list[str]:
        factors = [
            (
                f"Beklenen gol dengesi "
                f"{home_xg:.2f}-{away_xg:.2f}"
            ),
            (
                f"Kulüp son form puanı "
                f"{club_profile.form_rating:.2f}"
            ),
            (
                f"Rakip son form puanı "
                f"{opponent.form_rating:.2f}"
            ),
        ]
        if match.venue == "HOME":
            factors.append("Ev sahibi avantajı modele eklendi")
        else:
            factors.append("Deplasman dezavantajı modele eklendi")
        if unavailable_impact > 0:
            factors.append(
                f"Kulüp eksik oyuncu etkisi "
                f"%{unavailable_impact * 100:.0f}"
            )
        if opponent_unavailable_impact > 0:
            factors.append(
                f"Rakip eksik oyuncu etkisi "
                f"%{opponent_unavailable_impact * 100:.0f}"
            )
        return factors

    def _risks(
        self,
        *,
        club_profile,
        opponent,
        unavailable_impact,
    ) -> list[str]:
        risks = []
        if club_profile.sample_size < 5:
            risks.append(
                "Kulüp için örneklem düşük; tahmin güveni sınırlı"
            )
        if opponent.sample_size < 5:
            risks.append(
                "Rakip için örneklem düşük; güç profili oynak olabilir"
            )
        if unavailable_impact >= 0.25:
            risks.append(
                "Önemli oyuncu eksikleri tahmini ciddi biçimde etkiliyor"
            )
        if not risks:
            risks.append(
                "Tahmin; kadro, taktik ve maç içi olaylarla değişebilir"
            )
        return risks

    def _result(self, home_goals: int, away_goals: int) -> str:
        if home_goals > away_goals:
            return "HOME"
        if home_goals < away_goals:
            return "AWAY"
        return "DRAW"

    def _clamp(
        self,
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        return max(minimum, min(maximum, value))
