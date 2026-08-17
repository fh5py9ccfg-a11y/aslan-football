import json
import logging

from sqlalchemy import text
from .db import SessionLocal

from pydantic import BaseModel
from pathlib import Path
from fastapi.responses import FileResponse, StreamingResponse
from fastapi import (
    Depends,
    FastAPI,
    HTTPException,
    Query,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
logger = logging.getLogger(__name__)

from .disaster_recovery import RedisDisasterRecoveryRepository
from .dr_coordinator import DisasterRecoveryCoordinator
from .session_maintenance import SessionMaintenanceWorker
from .session_maintenance import RedisSessionIndexMaintainer
from .distributed_lease import RedisLease
from .compensation import RedisCompensationRepository
from .compensation_orchestrator import CompensationHandlerRegistry, CompensationOrchestrator, CompensationWorker
from .compensation_execution import RedisCompensationExecutionRepository
from .compensation_outbox import RedisCompensationCommitter
from .compensation_outbox_publisher import RedisOutboxDeliveryRepository
from .outbox_receipts import RedisPublishReceiptRepository
from .transport_circuit_breaker import RedisCircuitBreaker
from .outbox_transport import build_outbox_transport
from .event_ordering import RedisEventOrderingRepository
from .compensation_outbox_publisher import OutboxPublisherWorker, CompensationOutboxPublisher
from .idempotent_closure import IdempotentClosureExecutor
from .idempotent_effects import RedisIdempotentEffectRepository
from fastapi.responses import PlainTextResponse
from football_core import MatchEvent, MatchStateService

from .api_keys import (
    configure_api_key_registry,
    current_registry,
    provider_api_key,
)
from .api_key_registry import RedisApiKeyRegistry
from .alert_policy import (
    AlertIncidentService,
    AlertPolicy,
    RedisAlertPolicyRepository,
    SilenceRule,
)
from .alerting import (
    AlertDeliveryService,
    AlertMessage,
    AlertSubscription,
    RedisAlertRepository,
    WebhookDeliveryClient,
)
from .audit import make_audit_event
from .claim_mapping import ClaimMapper, ClaimMapping
from .identity_gateway import IdentityGateway, UnifiedPrincipal
from .jwt_tokens import JwtPrincipal, JwtTokenService, SigningKeyRing
from .jwks import JwksCache
from .oidc import OidcTokenVerifier
from .oidc_discovery import OidcDiscoveryCache
from .oidc_refresh import OidcMetadataRefresher
from .refresh_sessions import (
    InMemoryRefreshSessionRepository,
    RedisRefreshSessionRepository,
    RefreshReuseDetected,
)
from .lifecycle import (
    build_audit_repository,
    lifespan,
)
from .maintenance_journal import RedisMaintenanceJournal
from .quarantine_diagnostics import RedisQuarantineDiagnosticService
from .quarantine_management import RedisQuarantineManager
from .quarantine_retry import QuarantineRetryService
from .quarantine_verification import (
    QuarantineVerificationService,
    RedisRemediationEvidenceRepository,
)
from .dual_control_closure import DualControlQuarantineClosureService
from .quorum_approval import (
    DuplicateVote,
    RedisQuorumApprovalRepository,
)
from .quorum_closure import QuorumQuarantineClosureService
from .quorum_execution import RedisQuorumExecutionRepository
from .quorum_risk_policy import QuorumRiskPolicyEngine
from .quarantine_approval import (
    ApprovalConflict,
    ApprovalExpired,
    RedisQuarantineApprovalRepository,
)
from .quarantine_closure import VerifiedQuarantineClosureService
from .maintenance_progress import RedisMaintenanceProgressRepository
from .metrics import metrics
from .drain_mode import DrainController, drain_middleware
from .self_healing import (
    RedisSelfHealingRepository,
    SelfHealingOrchestrator,
)
from .self_healing_worker import SelfHealingWorker
from .rolling_upgrade import (
    IncompatibleRelease,
    RedisRollingUpgradeRepository,
    RollingUpgradeCoordinator,
    UpgradeConflict,
)
from .observability import (
    configure_logging,
    correlation_id_var,
    correlation_middleware,
)
from .rate_limit import SlidingWindowRateLimiter
from .readiness import database_ready, provider_ready
from .repository_factory import build_event_repository
from .provider_gateway import (
    EventReconciler,
    GenericJsonProviderAdapter,
    ProviderGateway,
    ProviderQualityEngine,
    ProviderTrustRepository,
    RawProviderEvent,
)
from .postmortem_knowledge import (
    PostmortemKnowledgeService,
    RedisPostmortemRepository,
)
from .prediction_confidence import (
    PredictionConfidenceAdjuster,
)
from .release_guard import (
    RedisReleaseGuardRepository,
    ReleaseGuardService,
)
from .reliability_management import (
    RedisReliabilityRepository,
    ReliabilityManagementService,
)
from .compliance_attestation import (
    ComplianceAttestationService,
    RedisComplianceAttestationRepository,
)
from .final_pilot import FinalPilotService
from .pilot_acceptance import PilotAcceptanceService
from .rolling_team_model import (
    RollingModel,
    RollingTeamModelService,
)
from .ensemble_training import (
    EnsembleModel,
    EnsembleTrainingService,
)
from .real_data_training import (
    RealDataTrainingService,
    RealDataValidationError,
)
from .supply_chain_security import (
    SupplyChainSecurityService,
    SupplyChainValidationError,
)
from .release_freeze import (
    ReleaseFreezeService,
    ReleaseFreezeValidationError,
)
from .delivery_hardening import (
    DeliveryHardeningService,
    DeliveryHardeningValidationError,
)
from .pilot_experiments import (
    ExperimentValidationError,
    PilotExperimentService,
    RedisPilotExperimentRepository,
)
from .pilot_product_analytics import (
    PilotProductAnalyticsService,
    ProductAnalyticsValidationError,
    RedisPilotProductAnalyticsRepository,
)
from .pilot_observability import (
    ObservabilityValidationError,
    PilotObservabilityService,
    RedisPilotObservabilityRepository,
)
from .pilot_stabilization import (
    PilotStabilizationService,
)
from .match_intelligence import (
    MatchIntelligenceService,
    MatchIntelligenceValidationError,
    RedisMatchIntelligenceRepository,
)
from .mvp_integrations import (
    IntegrationValidationError,
    MVPIntegrationService,
    RedisMVPIntegrationRepository,
)
from .mvp_auth import (
    MVPAuthError, MVPAuthService, RedisMVPAuthRepository,
)
from .mvp_workspace import (
    MVPWorkspaceService,
    RedisMVPRepository,
)
from .audit_orchestration import (
    AuditOrchestrationService,
    RedisAuditOrchestrationRepository,
)
from .continuous_compliance import (
    ContinuousComplianceService,
    RedisContinuousComplianceRepository,
)
from .governance_exceptions import (
    GovernanceExceptionService,
    RedisGovernanceExceptionRepository,
)
from .governance import (
    GovernanceService,
    RedisGovernanceRepository,
)
from .transparency_witness import (
    CheckpointConsistencyProof,
    RedisTransparencyWitnessRepository,
    TransparencyWitnessService,
)
from .transparency_log import (
    InclusionProof,
    RedisTransparencyLogRepository,
    TransparencyLogService,
)
from .change_management import (
    ChangeManagementService,
    RedisChangeManagementRepository,
)
from .deployment_safety import (
    DeploymentSafetyService,
    RedisDeploymentSafetyRepository,
)
from .deployment_verification import (
    DeploymentVerificationService,
    RedisDeploymentVerificationRepository,
)
from .progressive_delivery import (
    ProgressiveDeliveryService,
    RedisProgressiveDeliveryRepository,
)
from .production_readiness import (
    MaintenanceController,
    OperationalCertification,
    ProductionReadinessValidator,
    ReadinessCheck,
)
from .feature_store import (
    FeatureDefinition,
    FeatureLineageService,
    FeatureValue,
    RedisFeatureStore,
)
from .model_deployment import ModelDeploymentManager
from .model_evaluation import (
    ModelEvaluator,
    ProbabilityCalibrator,
)
from .model_monitoring import (
    ModelMonitoringService,
    RedisModelMonitoringRepository,
)
from .model_registry import RedisModelRegistry
from .streaming_analytics import (
    LiveMatchEvent,
    RedisStreamingRepository,
    StreamingAnalyticsEngine,
)
from .inference_platform import (
    AdaptiveInferenceRouter,
    InferenceRequest,
    InferenceService,
    InMemoryModelRuntime,
    MicroBatcher,
    ModelRuntimeRegistry,
    RedisPredictionCache,
)
from .live_decision_orchestrator import (
    LiveDecisionOrchestrator,
    RedisLiveDecisionRepository,
)
from .maintenance_mode import maintenance_mode_middleware
from .release_manifest import (
    ReleaseCertification,
    ReleaseComponent,
    ReleaseManifestBuilder,
)
from .sbom import SbomBuilder, SoftwareComponent
from .request_limits import request_size_middleware
from .schemas import EventIn, MatchStateOut
from .revocation import InMemoryRevocationRepository
from .redis_security import (
    RedisRevocationRepository,
    RedisWebSocketTicketRepository,
    build_security_redis_client,
)
from .security_headers import (
    security_headers_middleware,
)
from .settings import settings
from .saga import RedisSagaRepository, SagaHandlerRegistry, SagaOrchestrator
from .token_bucket import (
    build_token_bucket_limiter,
    token_bucket_middleware,
)
from .ws_tickets import InMemoryWebSocketTicketRepository

configure_logging()

class MobileQuickPredictionRequest(BaseModel):
    home_team: str = "Ev Takımı"
    away_team: str = "Deplasman Takımı"
    home_xg: float
    away_xg: float
    home_elo: float
    away_elo: float
    home_form: float = 0.5
    away_form: float = 0.5


app = FastAPI(
    title=settings.app_name,
    version="v1.3.0-rolling-model",
    lifespan=lifespan,
)
app.state.shutting_down = False
app.state.drain_controller = DrainController()
app.state.rolling_upgrade_coordinator = None
app.state.self_healing_orchestrator = None
app.state.self_healing_worker = None
app.state.maintenance_controller = MaintenanceController()
app.state.production_readiness_validator = (
    ProductionReadinessValidator(
        environment=settings.environment,
        required_variables=(
            ("AUTH_TOKEN_SECRET",)
            if settings.environment == "production"
            else ()
        ),
    )
)
app.state.operational_certification = None
app.state.release_manifest_builder = ReleaseManifestBuilder()
app.state.release_certification = None
app.state.sbom_builder = SbomBuilder()
app.state.provider_gateway = None
app.state.model_registry = None
app.state.model_deployment_manager = None
app.state.model_evaluator = ModelEvaluator()
app.state.model_monitoring_service = None
app.state.feature_store = None
app.state.feature_lineage_service = None
app.state.model_runtime_registry = (
    ModelRuntimeRegistry()
)
app.state.inference_service = None
app.state.micro_batcher = None
app.state.streaming_analytics_engine = None
app.state.live_decision_orchestrator = None
app.state.alert_repository = None
app.state.alert_delivery_service = None
app.state.alert_policy_repository = None
app.state.alert_incident_service = None
app.state.postmortem_repository = None
app.state.postmortem_service = None
app.state.reliability_service = None
app.state.release_guard_service = None
app.state.progressive_delivery_service = None
app.state.deployment_verification_service = None
app.state.deployment_safety_service = None
app.state.change_management_service = None
app.state.transparency_log_service = None
app.state.transparency_witness_service = None
app.state.governance_service = None
app.state.governance_exception_service = None
app.state.continuous_compliance_service = None
app.state.audit_orchestration_service = None
app.state.mvp_workspace_service = None
app.state.mvp_auth_service = None
app.state.mvp_integration_service = None
app.state.match_intelligence_service = None
app.state.pilot_stabilization_service = None
app.state.pilot_observability_service = None
app.state.pilot_product_analytics_service = None
app.state.pilot_experiment_service = None
app.state.final_pilot_service = None
app.state.pilot_acceptance_service = None
app.state.delivery_hardening_service = None
app.state.release_freeze_service = None
app.state.supply_chain_security_service = None
app.state.real_data_training_service = None
app.state.ensemble_training_service = None
app.state.rolling_team_model_service = None
app.state.compliance_attestation_service = None
app.state.probability_calibrator = (
    ProbabilityCalibrator()
)
app.state.prediction_confidence_adjuster = (
    PredictionConfidenceAdjuster()
)
if settings.environment == "test":
    app.state.revocations = InMemoryRevocationRepository()
    app.state.ws_tickets = InMemoryWebSocketTicketRepository()
    app.state.api_key_registry = current_registry()
else:
    try:
        security_redis = build_security_redis_client()
        app.state.revocations = RedisRevocationRepository(
            security_redis
        )
        app.state.ws_tickets = RedisWebSocketTicketRepository(
            security_redis
        )
        app.state.api_key_registry = RedisApiKeyRegistry(
            security_redis
        )
    except Exception:
        app.state.revocations = InMemoryRevocationRepository()
        app.state.ws_tickets = InMemoryWebSocketTicketRepository()
        app.state.api_key_registry = current_registry()

configure_api_key_registry(app.state.api_key_registry)

try:
    upgrade_redis = security_redis
except NameError:
    class _InMemoryUpgradeRedis:
        def __init__(self):
            self.values = {}

        def get(self, key):
            return self.values.get(key)

        def eval(self, script, number_of_keys, *args):
            key = args[0]
            expected_generation = int(args[1])
            payload = args[2]
            existing = self.values.get(key)
            if existing is not None:
                import json as _json
                current = _json.loads(existing)
                if int(current["current_generation"]) != expected_generation:
                    return [0, existing]
            elif expected_generation != 0:
                return [0, "missing"]
            self.values[key] = payload
            return [1, payload]

    upgrade_redis = _InMemoryUpgradeRedis()

app.state.rolling_upgrade_coordinator = RollingUpgradeCoordinator(
    repository=RedisRollingUpgradeRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "ROLLING_UPGRADE_PREFIX",
            "aslan:rolling-upgrade",
        ),
    )
)






app.state.model_runtime_registry.register(
    InMemoryModelRuntime(
        model_id="baseline-v1",
        weight=0.8,
        bias=0.1,
    )
)
app.state.model_runtime_registry.register(
    InMemoryModelRuntime(
        model_id="fallback-v1",
        weight=0.6,
        bias=0.2,
    )
)
app.state.inference_service = InferenceService(
    runtime_registry=app.state.model_runtime_registry,
    router=AdaptiveInferenceRouter(
        deployment_manager=(
            app.state.model_deployment_manager
        )
    ),
    cache=RedisPredictionCache(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "PREDICTION_CACHE_PREFIX",
            "aslan:prediction-cache",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "PREDICTION_CACHE_TTL_SECONDS",
                "30",
            )
        ),
    ),
    timeout_seconds=float(
        __import__("os").getenv(
            "INFERENCE_TIMEOUT_SECONDS",
            "1.0",
        )
    ),
)
app.state.micro_batcher = MicroBatcher(
    service=app.state.inference_service,
    max_batch_size=int(
        __import__("os").getenv(
            "INFERENCE_MAX_BATCH_SIZE",
            "16",
        )
    ),
)

app.state.streaming_analytics_engine = StreamingAnalyticsEngine(
    repository=RedisStreamingRepository(
        upgrade_redis,
        prefix=__import__("os").getenv("STREAMING_ANALYTICS_PREFIX", "aslan:streaming"),
        ttl_seconds=int(__import__("os").getenv("STREAMING_ANALYTICS_TTL_SECONDS", "86400")),
    ),
    allowed_lateness_seconds=int(__import__("os").getenv("STREAMING_ALLOWED_LATENESS_SECONDS", "10")),
    decision_threshold=float(__import__("os").getenv("STREAMING_DECISION_THRESHOLD", "4.0")),
)


app.state.live_decision_orchestrator = LiveDecisionOrchestrator(
    repository=RedisLiveDecisionRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "LIVE_DECISION_PREFIX",
            "aslan:live-decision",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "LIVE_DECISION_TTL_SECONDS",
                "604800",
            )
        ),
    ),
    inference_service=app.state.inference_service,
    cooldown_seconds=int(
        __import__("os").getenv(
            "LIVE_DECISION_COOLDOWN_SECONDS",
            "30",
        )
    ),
    max_attempts=int(
        __import__("os").getenv(
            "LIVE_DECISION_MAX_ATTEMPTS",
            "2",
        )
    ),
)


async def _default_webhook_sender(destination, payload):
    return 202

app.state.alert_repository = RedisAlertRepository(
    upgrade_redis,
    prefix=__import__("os").getenv("ALERTING_PREFIX", "aslan:alerting"),
    ttl_seconds=int(__import__("os").getenv("ALERTING_TTL_SECONDS", "2592000")),
)
app.state.alert_delivery_service = AlertDeliveryService(
    repository=app.state.alert_repository,
    client=WebhookDeliveryClient(_default_webhook_sender),
    max_attempts=int(__import__("os").getenv("ALERTING_MAX_ATTEMPTS", "3")),
    backoff_seconds=float(__import__("os").getenv("ALERTING_BACKOFF_SECONDS", "0.01")),
)


app.state.alert_policy_repository = (
    RedisAlertPolicyRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "ALERT_POLICY_PREFIX",
            "aslan:alert-policy",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "ALERT_POLICY_TTL_SECONDS",
                "7776000",
            )
        ),
    )
)
app.state.alert_incident_service = AlertIncidentService(
    repository=app.state.alert_policy_repository
)


app.state.postmortem_repository = (
    RedisPostmortemRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "POSTMORTEM_PREFIX",
            "aslan:postmortem",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "POSTMORTEM_TTL_SECONDS",
                "31536000",
            )
        ),
    )
)
app.state.postmortem_service = (
    PostmortemKnowledgeService(
        repository=app.state.postmortem_repository,
        incident_repository=(
            app.state.alert_policy_repository
        ),
    )
)


app.state.reliability_service = ReliabilityManagementService(
    repository=RedisReliabilityRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "RELIABILITY_PREFIX",
            "aslan:reliability",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "RELIABILITY_TTL_SECONDS",
                "31536000",
            )
        ),
    )
)


app.state.release_guard_service = ReleaseGuardService(
    repository=RedisReleaseGuardRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "RELEASE_GUARD_PREFIX",
            "aslan:release-guard",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "RELEASE_GUARD_TTL_SECONDS",
                "31536000",
            )
        ),
    ),
    reliability_service=app.state.reliability_service,
)


app.state.progressive_delivery_service = (
    ProgressiveDeliveryService(
        repository=RedisProgressiveDeliveryRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "PROGRESSIVE_DELIVERY_PREFIX",
                "aslan:progressive-delivery",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "PROGRESSIVE_DELIVERY_TTL_SECONDS",
                    "31536000",
                )
            ),
        ),
        reliability_service=(
            app.state.reliability_service
        ),
        release_guard_service=(
            app.state.release_guard_service
        ),
    )
)


app.state.deployment_verification_service = (
    DeploymentVerificationService(
        repository=RedisDeploymentVerificationRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "DEPLOYMENT_VERIFICATION_PREFIX",
                "aslan:deployment-verification",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "DEPLOYMENT_VERIFICATION_TTL_SECONDS",
                    "31536000",
                )
            ),
        ),
        progressive_delivery_service=(
            app.state.progressive_delivery_service
        ),
        deployment_manager=(
            app.state.model_deployment_manager
        ),
    )
)


app.state.deployment_safety_service = (
    DeploymentSafetyService(
        repository=RedisDeploymentSafetyRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "DEPLOYMENT_SAFETY_PREFIX",
                "aslan:deployment-safety",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "DEPLOYMENT_SAFETY_TTL_SECONDS",
                    "31536000",
                )
            ),
        ),
        reliability_service=(
            app.state.reliability_service
        ),
        progressive_delivery_service=(
            app.state.progressive_delivery_service
        ),
        deployment_verification_service=(
            app.state.deployment_verification_service
        ),
    )
)

app.state.change_management_service = ChangeManagementService(
    repository=RedisChangeManagementRepository(
        upgrade_redis,
        prefix=__import__("os").getenv("CHANGE_MANAGEMENT_PREFIX", "aslan:change-management"),
        ttl_seconds=int(__import__("os").getenv("CHANGE_MANAGEMENT_TTL_SECONDS", "31536000")),
    ),
    deployment_verification_service=app.state.deployment_verification_service,
    deployment_safety_service=app.state.deployment_safety_service,
)

app.state.compliance_attestation_service = ComplianceAttestationService(
    repository=RedisComplianceAttestationRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "COMPLIANCE_ATTESTATION_PREFIX",
            "aslan:compliance-attestation",
        ),
        ttl_seconds=int(__import__("os").getenv("COMPLIANCE_ATTESTATION_TTL_SECONDS", "31536000")),
    ),
    change_management_service=app.state.change_management_service,
    signing_keys={
        __import__("os").getenv("COMPLIANCE_ATTESTATION_KEY_ID", "local-v1"):
        __import__("os").getenv("COMPLIANCE_ATTESTATION_SECRET", "test-attestation-secret")
    },
    active_key_id=__import__("os").getenv("COMPLIANCE_ATTESTATION_KEY_ID", "local-v1"),
)


app.state.transparency_log_service = (
    TransparencyLogService(
        repository=RedisTransparencyLogRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "TRANSPARENCY_LOG_PREFIX",
                "aslan:transparency-log",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "TRANSPARENCY_LOG_TTL_SECONDS",
                    "31536000",
                )
            ),
        ),
        change_management_service=(
            app.state.change_management_service
        ),
        compliance_attestation_service=(
            app.state.compliance_attestation_service
        ),
    )
)


app.state.transparency_witness_service = (
    TransparencyWitnessService(
        repository=RedisTransparencyWitnessRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "TRANSPARENCY_WITNESS_PREFIX",
                "aslan:transparency-witness",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "TRANSPARENCY_WITNESS_TTL_SECONDS",
                    "31536000",
                )
            ),
        ),
        transparency_log_service=(
            app.state.transparency_log_service
        ),
    )
)

app.state.governance_service = GovernanceService(
    repository=RedisGovernanceRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "GOVERNANCE_PREFIX",
            "aslan:governance",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "GOVERNANCE_TTL_SECONDS",
                "31536000",
            )
        ),
    )
)


app.state.governance_exception_service = (
    GovernanceExceptionService(
        repository=RedisGovernanceExceptionRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "GOVERNANCE_EXCEPTION_PREFIX",
                "aslan:governance-exceptions",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "GOVERNANCE_EXCEPTION_TTL_SECONDS",
                    "31536000",
                )
            ),
        ),
        governance_service=app.state.governance_service,
    )
)


app.state.continuous_compliance_service = (
    ContinuousComplianceService(
        repository=RedisContinuousComplianceRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "CONTINUOUS_COMPLIANCE_PREFIX",
                "aslan:continuous-compliance",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "CONTINUOUS_COMPLIANCE_TTL_SECONDS",
                    "31536000",
                )
            ),
        ),
        governance_service=(
            app.state.governance_service
        ),
        governance_exception_service=(
            app.state.governance_exception_service
        ),
    )
)


app.state.audit_orchestration_service = (
    AuditOrchestrationService(
        repository=RedisAuditOrchestrationRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "AUDIT_ORCHESTRATION_PREFIX",
                "aslan:audit-orchestration",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "AUDIT_ORCHESTRATION_TTL_SECONDS",
                    "31536000",
                )
            ),
        ),
        governance_service=app.state.governance_service,
    )
)


app.state.mvp_workspace_service = MVPWorkspaceService(
    repository=RedisMVPRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "MVP_WORKSPACE_PREFIX",
            "aslan:mvp",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "MVP_WORKSPACE_TTL_SECONDS",
                "31536000",
            )
        ),
    )
)

app.state.mvp_auth_service = MVPAuthService(
    repository=RedisMVPAuthRepository(upgrade_redis, prefix=__import__("os").getenv("MVP_AUTH_PREFIX","aslan:mvp-auth"), ttl_seconds=int(__import__("os").getenv("MVP_AUTH_TTL_SECONDS","86400"))),
    secret=__import__("os").getenv("MVP_AUTH_SECRET","local-pilot-secret-change-me"),
)
app.state.mvp_auth_service.ensure_demo_users()


app.state.mvp_integration_service = MVPIntegrationService(
    repository=RedisMVPIntegrationRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "MVP_INTEGRATION_PREFIX",
            "aslan:mvp-integrations",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "MVP_INTEGRATION_TTL_SECONDS",
                "31536000",
            )
        ),
    ),
    workspace_service=app.state.mvp_workspace_service,
)


app.state.match_intelligence_service = MatchIntelligenceService(
    repository=RedisMatchIntelligenceRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "MATCH_INTELLIGENCE_PREFIX",
            "aslan:match-intelligence",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "MATCH_INTELLIGENCE_TTL_SECONDS",
                "31536000",
            )
        ),
    ),
    workspace_service=app.state.mvp_workspace_service,
)


app.state.pilot_stabilization_service = PilotStabilizationService(
    workspace_service=app.state.mvp_workspace_service,
    intelligence_service=app.state.match_intelligence_service,
)


app.state.pilot_observability_service = PilotObservabilityService(
    repository=RedisPilotObservabilityRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "PILOT_OBSERVABILITY_PREFIX",
            "aslan:pilot-observability",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "PILOT_OBSERVABILITY_TTL_SECONDS",
                "31536000",
            )
        ),
    ),
    intelligence_service=app.state.match_intelligence_service,
)


app.state.pilot_product_analytics_service = PilotProductAnalyticsService(
    repository=RedisPilotProductAnalyticsRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "PILOT_PRODUCT_ANALYTICS_PREFIX",
            "aslan:pilot-product-analytics",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "PILOT_PRODUCT_ANALYTICS_TTL_SECONDS",
                "31536000",
            )
        ),
    ),
)


app.state.pilot_experiment_service = PilotExperimentService(
    repository=RedisPilotExperimentRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "PILOT_EXPERIMENT_PREFIX",
            "aslan:pilot-experiments",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "PILOT_EXPERIMENT_TTL_SECONDS",
                "31536000",
            )
        ),
    ),
)


app.state.final_pilot_service = FinalPilotService(
    workspace_service=app.state.mvp_workspace_service,
    intelligence_service=app.state.match_intelligence_service,
    observability_service=app.state.pilot_observability_service,
)


app.state.pilot_acceptance_service = PilotAcceptanceService(
    final_pilot_service=app.state.final_pilot_service,
    stabilization_service=app.state.pilot_stabilization_service,
    observability_service=app.state.pilot_observability_service,
    intelligence_service=app.state.match_intelligence_service,
)


app.state.delivery_hardening_service = DeliveryHardeningService()

app.state.release_freeze_service = ReleaseFreezeService()

app.state.supply_chain_security_service = SupplyChainSecurityService()

app.state.real_data_training_service = RealDataTrainingService()

app.state.ensemble_training_service = EnsembleTrainingService()

app.state.rolling_team_model_service = RollingTeamModelService()

app.state.feature_store = RedisFeatureStore(
    upgrade_redis,
    prefix=__import__("os").getenv(
        "FEATURE_STORE_PREFIX",
        "aslan:feature-store",
    ),
    offline_limit=int(
        __import__("os").getenv(
            "FEATURE_STORE_OFFLINE_LIMIT",
            "1000",
        )
    ),
)
app.state.feature_lineage_service = (
    FeatureLineageService(
        store=app.state.feature_store
    )
)

app.state.model_monitoring_service = ModelMonitoringService(
    repository=RedisModelMonitoringRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "MODEL_MONITORING_PREFIX",
            "aslan:model-monitoring",
        ),
    )
)

app.state.model_registry = RedisModelRegistry(
    upgrade_redis,
    prefix=__import__("os").getenv(
        "MODEL_REGISTRY_PREFIX",
        "aslan:model-registry",
    ),
)
app.state.model_deployment_manager = (
    ModelDeploymentManager(
        upgrade_redis,
        registry=app.state.model_registry,
        prefix=__import__("os").getenv(
            "MODEL_DEPLOYMENT_PREFIX",
            "aslan:model-deployment",
        ),
    )
)

app.state.provider_gateway = ProviderGateway(
    adapters=(
        GenericJsonProviderAdapter("sportmonks"),
        GenericJsonProviderAdapter("stats-provider"),
    ),
    quality_engine=ProviderQualityEngine(
        repository=ProviderTrustRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "PROVIDER_TRUST_PREFIX",
                "aslan:provider-trust",
            ),
        )
    ),
    reconciler=EventReconciler(
        trust_repository=ProviderTrustRepository(
            upgrade_redis,
            prefix=__import__("os").getenv(
                "PROVIDER_TRUST_PREFIX",
                "aslan:provider-trust",
            ),
        ),
        timestamp_tolerance_seconds=int(
            __import__("os").getenv(
                "PROVIDER_EVENT_TOLERANCE_SECONDS",
                "5",
            )
        ),
    ),
)

app.state.self_healing_orchestrator = SelfHealingOrchestrator(
    repository=RedisSelfHealingRepository(
        upgrade_redis,
        prefix=__import__("os").getenv(
            "SELF_HEALING_PREFIX",
            "aslan:self-healing",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "SELF_HEALING_TTL_SECONDS",
                "604800",
            )
        ),
    ),
    heartbeat_timeout_seconds=int(
        __import__("os").getenv(
            "SELF_HEALING_HEARTBEAT_TIMEOUT_SECONDS",
            "60",
        )
    ),
    quarantine_seconds=int(
        __import__("os").getenv(
            "SELF_HEALING_QUARANTINE_SECONDS",
            "300",
        )
    ),
    unhealthy_score=int(
        __import__("os").getenv(
            "SELF_HEALING_UNHEALTHY_SCORE",
            "35",
        )
    ),
    degraded_score=int(
        __import__("os").getenv(
            "SELF_HEALING_DEGRADED_SCORE",
            "65",
        )
    ),
)
app.state.self_healing_worker = SelfHealingWorker(
    orchestrator=app.state.self_healing_orchestrator,
    interval_seconds=float(
        __import__("os").getenv(
            "SELF_HEALING_INTERVAL_SECONDS",
            "30",
        )
    ),
)

app.state.operational_certification = OperationalCertification(
    readiness_validator=app.state.production_readiness_validator,
    maintenance_controller=app.state.maintenance_controller,
    self_healing_orchestrator=(
        app.state.self_healing_orchestrator
    ),
    dr_repository=getattr(
        app.state,
        "dr_repository",
        None,
    ),
)

app.state.release_certification = ReleaseCertification(
    manifest_builder=app.state.release_manifest_builder,
    operational_certification=(
        app.state.operational_certification
    ),
)



app.state.jwt_key_ring = SigningKeyRing()
app.state.jwt_key_ring.add(
    key_id=__import__('os').getenv('JWT_ACTIVE_KID', 'local-v1'),
    secret=__import__('os').getenv('AUTH_TOKEN_SECRET', 'development-secret-change-me'),
    activate=True,
)
app.state.token_service = JwtTokenService(
    key_ring=app.state.jwt_key_ring,
    issuer=__import__('os').getenv('JWT_ISSUER', 'aslan-ozaslan'),
    audience=__import__('os').getenv('JWT_AUDIENCE', 'aslan-platform'),
    revocation_repository=app.state.revocations,
)
if settings.environment == "test":
    app.state.refresh_sessions = (
        InMemoryRefreshSessionRepository()
    )
else:
    try:
        app.state.refresh_sessions = (
            RedisRefreshSessionRepository(
                security_redis
            )
        )
    except Exception:
        app.state.refresh_sessions = (
            InMemoryRefreshSessionRepository()
        )

oidc_issuer = __import__("os").getenv(
    "OIDC_ISSUER",
    "",
).strip()
oidc_audience = __import__("os").getenv(
    "OIDC_AUDIENCE",
    "",
).strip()
oidc_jwks_url = __import__("os").getenv(
    "OIDC_JWKS_URL",
    "",
).strip()
oidc_discovery_enabled = (
    __import__("os").getenv(
        "OIDC_DISCOVERY_ENABLED",
        "true",
    ).lower()
    in {"1", "true", "yes"}
)

app.state.oidc_discovery_cache = None
app.state.oidc_jwks_cache = None
app.state.oidc_verifier = None

if oidc_issuer and oidc_audience:
    if oidc_discovery_enabled and not oidc_jwks_url:
        app.state.oidc_discovery_cache = (
            OidcDiscoveryCache(
                issuer=oidc_issuer,
                ttl_seconds=int(
                    __import__("os").getenv(
                        "OIDC_DISCOVERY_CACHE_SECONDS",
                        "3600",
                    )
                ),
                stale_if_error_seconds=int(
                    __import__("os").getenv(
                        "OIDC_DISCOVERY_STALE_SECONDS",
                        "21600",
                    )
                ),
            )
        )
        oidc_jwks_url = (
            app.state
            .oidc_discovery_cache
            .get()
            .jwks_uri
        )

    if oidc_jwks_url:
        app.state.oidc_jwks_cache = JwksCache(
            jwks_url=oidc_jwks_url,
            ttl_seconds=int(
                __import__("os").getenv(
                    "OIDC_JWKS_CACHE_SECONDS",
                    "300",
                )
            ),
            stale_if_error_seconds=int(
                __import__("os").getenv(
                    "OIDC_JWKS_STALE_SECONDS",
                    "3600",
                )
            ),
        )
        allowed_issuers = tuple(
            item.strip()
            for item in __import__("os").getenv(
                "OIDC_ALLOWED_ISSUERS",
                oidc_issuer,
            ).split(",")
            if item.strip()
        )
        claim_mapper = ClaimMapper(
            ClaimMapping.from_json(
                __import__("os").getenv(
                    "OIDC_CLAIM_MAPPING_JSON"
                )
            )
        )
        app.state.oidc_verifier = OidcTokenVerifier(
            issuer=oidc_issuer,
            audience=oidc_audience,
            jwks_cache=app.state.oidc_jwks_cache,
            claim_mapper=claim_mapper,
            allowed_issuers=allowed_issuers,
        )

app.state.identity_gateway = IdentityGateway(
    local_service=app.state.token_service,
    oidc_verifier=app.state.oidc_verifier,
)

app.state.session_maintenance_worker = None
app.state.quarantine_manager = None
app.state.quarantine_diagnostics = None
app.state.quarantine_retry_service = None
app.state.quarantine_verification_service = None
app.state.quarantine_closure_service = None
app.state.quarantine_approval_repository = None
app.state.dual_control_closure_service = None
app.state.quorum_approval_repository = None
app.state.quorum_closure_service = None
app.state.quorum_execution_repository = None
app.state.quorum_risk_policy_engine = QuorumRiskPolicyEngine()
app.state.idempotent_closure_executor = None
app.state.compensation_repository = None
app.state.compensation_worker = None
app.state.compensation_execution_repository = None
app.state.compensation_committer = None
app.state.outbox_publisher_worker = None
app.state.outbox_delivery_repository = None
app.state.outbox_receipt_repository = None
app.state.outbox_circuit_breaker = None
app.state.event_ordering_repository = None
app.state.saga_repository = None
app.state.saga_orchestrator = None
app.state.dr_repository = None
app.state.dr_coordinator = None
if (
    settings.environment != "test"
    and app.state.refresh_sessions.__class__.__name__
    == "RedisRefreshSessionRepository"
):
    app.state.saga_repository = RedisSagaRepository(security_redis, prefix=__import__("os").getenv("SAGA_PREFIX", "aslan:saga"), ttl_seconds=int(__import__("os").getenv("SAGA_TTL_SECONDS", "2592000")))
    saga_registry = SagaHandlerRegistry()
    app.state.dr_repository = RedisDisasterRecoveryRepository(
        security_redis,
        prefix=__import__("os").getenv(
            "DR_PREFIX",
            "aslan:dr",
        ),
        max_rpo_seconds=int(
            __import__("os").getenv(
                "DR_MAX_RPO_SECONDS",
                "60",
            )
        ),
    )
    app.state.dr_coordinator = DisasterRecoveryCoordinator(
        repository=app.state.dr_repository,
        max_rto_seconds=int(
            __import__("os").getenv(
                "DR_MAX_RTO_SECONDS",
                "300",
            )
        ),
    )
    app.state.saga_orchestrator = SagaOrchestrator(repository=app.state.saga_repository, registry=saga_registry)
    app.state.quarantine_manager = RedisQuarantineManager(
        security_redis,
        journal_prefix=__import__("os").getenv(
            "SESSION_MAINTENANCE_JOURNAL_PREFIX",
            "aslan:maintenance:journal",
        ),
        fence_key=__import__("os").getenv(
            "SESSION_MAINTENANCE_FENCE_KEY",
            "aslan:maintenance:session-index:fence",
        ),
        audit_ttl_seconds=int(
            __import__("os").getenv(
                "SESSION_MAINTENANCE_QUARANTINE_AUDIT_TTL_SECONDS",
                "2592000",
            )
        ),
    )
    app.state.quarantine_diagnostics = RedisQuarantineDiagnosticService(
        security_redis,
        session_prefix=__import__("os").getenv(
            "REFRESH_SESSION_PREFIX",
            "aslan:refresh:session:",
        ),
        journal_prefix=__import__("os").getenv(
            "SESSION_MAINTENANCE_JOURNAL_PREFIX",
            "aslan:maintenance:journal",
        ),
    )
    app.state.session_maintenance_worker = (
        SessionMaintenanceWorker(
            maintainer=RedisSessionIndexMaintainer(
                security_redis,
                progress_repository=(
                    RedisMaintenanceProgressRepository(
                        security_redis,
                        key=__import__("os").getenv(
                            "SESSION_MAINTENANCE_PROGRESS_KEY",
                            "aslan:maintenance:session-index:progress",
                        ),
                    )
                ),
                max_indexes_per_run=int(
                    __import__("os").getenv(
                        "SESSION_MAINTENANCE_MAX_INDEXES_PER_RUN",
                        "500",
                    )
                ),
                time_budget_seconds=float(
                    __import__("os").getenv(
                        "SESSION_MAINTENANCE_TIME_BUDGET_SECONDS",
                        "20",
                    )
                ),
                scan_count=int(
                    __import__("os").getenv(
                        "SESSION_MAINTENANCE_SCAN_COUNT",
                        "100",
                    )
                ),
                journal=RedisMaintenanceJournal(
                    security_redis,
                    prefix=__import__("os").getenv(
                        "SESSION_MAINTENANCE_JOURNAL_PREFIX",
                        "aslan:maintenance:journal",
                    ),
                    fence_key=__import__("os").getenv(
                        "SESSION_MAINTENANCE_FENCE_KEY",
                        "aslan:maintenance:session-index:fence",
                    ),
                    claim_ttl_seconds=int(
                        __import__("os").getenv(
                            "SESSION_MAINTENANCE_CLAIM_TTL_SECONDS",
                            "120",
                        )
                    ),
                    completed_ttl_seconds=int(
                        __import__("os").getenv(
                            "SESSION_MAINTENANCE_COMPLETED_TTL_SECONDS",
                            "86400",
                        )
                    ),
                    quarantine_ttl_seconds=int(
                        __import__("os").getenv(
                            "SESSION_MAINTENANCE_QUARANTINE_TTL_SECONDS",
                            "604800",
                        )
                    ),
                    max_attempts=int(
                        __import__("os").getenv(
                            "SESSION_MAINTENANCE_MAX_ATTEMPTS",
                            "3",
                        )
                    ),
                ),
            ),
            interval_seconds=float(
                __import__("os").getenv(
                    "SESSION_MAINTENANCE_INTERVAL_SECONDS",
                    "300",
                )
            ),
            lease=RedisLease(
                security_redis,
                key=__import__("os").getenv(
                    "SESSION_MAINTENANCE_LEASE_KEY",
                    "aslan:maintenance:session-index",
                ),
                ttl_seconds=int(
                    __import__("os").getenv(
                        "SESSION_MAINTENANCE_LEASE_TTL_SECONDS",
                        "120",
                    )
                ),
            ),
            lease_heartbeat_seconds=float(
                __import__("os").getenv(
                    "SESSION_MAINTENANCE_LEASE_HEARTBEAT_SECONDS",
                    "30",
                )
            ),
            jitter_seconds=float(
                __import__("os").getenv(
                    "SESSION_MAINTENANCE_JITTER_SECONDS",
                    "15",
                )
            ),
            error_backoff_seconds=float(
                __import__("os").getenv(
                    "SESSION_MAINTENANCE_ERROR_BACKOFF_SECONDS",
                    "30",
                )
            ),
            metrics=metrics,
            fence_key=__import__("os").getenv(
                "SESSION_MAINTENANCE_FENCE_KEY",
                "aslan:maintenance:session-index:fence",
            ),
        )
    )
    app.state.quarantine_retry_service = QuarantineRetryService(
        diagnostic_service=app.state.quarantine_diagnostics,
        maintainer_factory=lambda: RedisSessionIndexMaintainer(
            security_redis,
            max_indexes_per_run=1,
            time_budget_seconds=5,
            scan_count=1,
        ),
    )
    app.state.quarantine_verification_service = (
        QuarantineVerificationService(
            diagnostic_service=app.state.quarantine_diagnostics,
            retry_service=app.state.quarantine_retry_service,
            evidence_repository=RedisRemediationEvidenceRepository(
                security_redis,
                prefix=__import__("os").getenv(
                    "SESSION_MAINTENANCE_REMEDIATION_PREFIX",
                    "aslan:maintenance:remediation",
                ),
                fence_key=__import__("os").getenv(
                    "SESSION_MAINTENANCE_FENCE_KEY",
                    "aslan:maintenance:session-index:fence",
                ),
                ttl_seconds=int(
                    __import__("os").getenv(
                        "SESSION_MAINTENANCE_REMEDIATION_TTL_SECONDS",
                        "2592000",
                    )
                ),
            ),
        )
    )
    app.state.quarantine_closure_service = (
        VerifiedQuarantineClosureService(
            verification_service=(
                app.state.quarantine_verification_service
            ),
            quarantine_manager=app.state.quarantine_manager,
            progress_repository=(
                app.state
                .session_maintenance_worker
                .maintainer
                .progress_repository
            ),
        )
    )
    app.state.quarantine_approval_repository = (
        RedisQuarantineApprovalRepository(
            security_redis,
            prefix=__import__("os").getenv(
                "SESSION_MAINTENANCE_APPROVAL_PREFIX",
                "aslan:maintenance:approval",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "SESSION_MAINTENANCE_APPROVAL_TTL_SECONDS",
                    "1800",
                )
            ),
            signing_secret=__import__("os").getenv(
                "SESSION_MAINTENANCE_APPROVAL_SIGNING_SECRET",
                __import__("os").getenv(
                    "AUTH_TOKEN_SECRET",
                    "development-secret-change-me",
                ),
            ),
        )
    )
    app.state.dual_control_closure_service = (
        DualControlQuarantineClosureService(
            approval_repository=(
                app.state.quarantine_approval_repository
            ),
            closure_service=(
                app.state.quarantine_closure_service
            ),
        )
    )
    app.state.quorum_approval_repository = (
        RedisQuorumApprovalRepository(
            security_redis,
            prefix=__import__("os").getenv(
                "SESSION_MAINTENANCE_QUORUM_PREFIX",
                "aslan:maintenance:quorum",
            ),
            signing_secret=__import__("os").getenv(
                "SESSION_MAINTENANCE_APPROVAL_SIGNING_SECRET",
                __import__("os").getenv(
                    "AUTH_TOKEN_SECRET",
                    "development-secret-change-me",
                ),
            ),
        )
    )
    app.state.quorum_execution_repository = (
        RedisQuorumExecutionRepository(
            security_redis,
            prefix=__import__("os").getenv(
                "SESSION_MAINTENANCE_QUORUM_EXECUTION_PREFIX",
                "aslan:maintenance:quorum-execution",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "SESSION_MAINTENANCE_QUORUM_EXECUTION_TTL_SECONDS",
                    "2592000",
                )
            ),
            lease_seconds=int(
                __import__("os").getenv(
                    "SESSION_MAINTENANCE_QUORUM_EXECUTION_LEASE_SECONDS",
                    "60",
                )
            ),
        )
    )
    app.state.compensation_repository = RedisCompensationRepository(
        security_redis,
        prefix=__import__("os").getenv(
            "COMPENSATION_PREFIX",
            "aslan:compensation",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "COMPENSATION_TTL_SECONDS",
                "2592000",
            )
        ),
    )
    compensation_registry = CompensationHandlerRegistry()
    compensation_registry.register(
        "RECONCILE_QUARANTINE_CLOSURE",
        lambda record: None,
    )
    app.state.compensation_execution_repository = (
        RedisCompensationExecutionRepository(
            security_redis,
            prefix=__import__("os").getenv(
                "COMPENSATION_EXECUTION_PREFIX",
                "aslan:compensation-execution",
            ),
            lease_seconds=int(
                __import__("os").getenv(
                    "COMPENSATION_EXECUTION_LEASE_SECONDS",
                    "60",
                )
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "COMPENSATION_EXECUTION_TTL_SECONDS",
                    "2592000",
                )
            ),
        )
    )
    app.state.compensation_committer = RedisCompensationCommitter(
        security_redis,
        compensation_prefix=__import__("os").getenv(
            "COMPENSATION_PREFIX",
            "aslan:compensation",
        ),
        execution_prefix=__import__("os").getenv(
            "COMPENSATION_EXECUTION_PREFIX",
            "aslan:compensation-execution",
        ),
        outbox_prefix=__import__("os").getenv(
            "COMPENSATION_OUTBOX_PREFIX",
            "aslan:compensation-outbox",
        ),
        ttl_seconds=int(
            __import__("os").getenv(
                "COMPENSATION_OUTBOX_TTL_SECONDS",
                "2592000",
            )
        ),
    )
    app.state.outbox_delivery_repository = (
        RedisOutboxDeliveryRepository(
            security_redis,
            prefix=__import__("os").getenv(
                "COMPENSATION_OUTBOX_DELIVERY_PREFIX",
                "aslan:compensation-outbox-delivery",
            ),
            lease_seconds=int(
                __import__("os").getenv(
                    "COMPENSATION_OUTBOX_DELIVERY_LEASE_SECONDS",
                    "60",
                )
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "COMPENSATION_OUTBOX_DELIVERY_TTL_SECONDS",
                    "2592000",
                )
            ),
        )
    )
    app.state.outbox_receipt_repository = (
        RedisPublishReceiptRepository(
            security_redis,
            prefix=__import__("os").getenv(
                "COMPENSATION_OUTBOX_RECEIPT_PREFIX",
                "aslan:compensation-outbox-receipt",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "COMPENSATION_OUTBOX_RECEIPT_TTL_SECONDS",
                    "2592000",
                )
            ),
        )
    )
    app.state.outbox_circuit_breaker = RedisCircuitBreaker(
        security_redis,
        name="compensation-outbox-webhook",
        prefix=__import__("os").getenv(
            "COMPENSATION_OUTBOX_CIRCUIT_PREFIX",
            "aslan:circuit-breaker",
        ),
        failure_threshold=int(
            __import__("os").getenv(
                "COMPENSATION_OUTBOX_CIRCUIT_FAILURE_THRESHOLD",
                "5",
            )
        ),
        recovery_timeout_seconds=int(
            __import__("os").getenv(
                "COMPENSATION_OUTBOX_CIRCUIT_RECOVERY_SECONDS",
                "60",
            )
        ),
    )
    outbox_transport = build_outbox_transport(
        kind=__import__("os").getenv(
            "COMPENSATION_OUTBOX_TRANSPORT",
            "logging",
        ),
        logger=logger,
        webhook_url=__import__("os").getenv(
            "COMPENSATION_OUTBOX_WEBHOOK_URL",
            "",
        ),
        webhook_timeout_seconds=float(
            __import__("os").getenv(
                "COMPENSATION_OUTBOX_WEBHOOK_TIMEOUT_SECONDS",
                "5",
            )
        ),
        webhook_authorization_header=(
            __import__("os").getenv(
                "COMPENSATION_OUTBOX_WEBHOOK_AUTHORIZATION",
                "",
            )
            or None
        ),
        webhook_signing_secret=(
            __import__("os").getenv(
                "COMPENSATION_OUTBOX_WEBHOOK_SIGNING_SECRET",
                "",
            )
            or None
        ),
        circuit_breaker=(
            app.state.outbox_circuit_breaker
        ),
    )
    app.state.event_ordering_repository = RedisEventOrderingRepository(
        security_redis,
        prefix=__import__("os").getenv(
            "COMPENSATION_OUTBOX_ORDERING_PREFIX",
            "aslan:event-ordering",
        ),
        ttl_seconds=int(__import__("os").getenv(
            "COMPENSATION_OUTBOX_ORDERING_TTL_SECONDS",
            "2592000",
        )),
    )
    app.state.outbox_publisher_worker = OutboxPublisherWorker(
        publisher=CompensationOutboxPublisher(
            committer=app.state.compensation_committer,
            delivery_repository=(
                app.state.outbox_delivery_repository
            ),
            transport=outbox_transport,
            max_attempts=int(
                __import__("os").getenv(
                    "COMPENSATION_OUTBOX_MAX_ATTEMPTS",
                    "5",
                )
            ),
            base_backoff_seconds=int(
                __import__("os").getenv(
                    "COMPENSATION_OUTBOX_BASE_BACKOFF_SECONDS",
                    "30",
                )
            ),
            receipt_repository=(
                app.state.outbox_receipt_repository
            ),
            ordering_repository=app.state.event_ordering_repository,
            heartbeat_interval_seconds=float(
                __import__("os").getenv(
                    "COMPENSATION_OUTBOX_DELIVERY_HEARTBEAT_SECONDS",
                    "15",
                )
            ),
        ),
        interval_seconds=float(
            __import__("os").getenv(
                "COMPENSATION_OUTBOX_WORKER_INTERVAL_SECONDS",
                "10",
            )
        ),
        batch_size=int(
            __import__("os").getenv(
                "COMPENSATION_OUTBOX_WORKER_BATCH_SIZE",
                "100",
            )
        ),
    )
    compensation_orchestrator = CompensationOrchestrator(
        repository=app.state.compensation_repository,
        registry=compensation_registry,
        max_attempts=int(
            __import__("os").getenv(
                "COMPENSATION_MAX_ATTEMPTS",
                "5",
            )
        ),
        base_backoff_seconds=int(
            __import__("os").getenv(
                "COMPENSATION_BASE_BACKOFF_SECONDS",
                "30",
            )
        ),
        execution_repository=(
            app.state.compensation_execution_repository
        ),
        heartbeat_interval_seconds=float(
            __import__("os").getenv(
                "COMPENSATION_EXECUTION_HEARTBEAT_SECONDS",
                "15",
            )
        ),
        atomic_committer=app.state.compensation_committer,
    )
    app.state.compensation_worker = CompensationWorker(
        repository=app.state.compensation_repository,
        orchestrator=compensation_orchestrator,
        interval_seconds=float(
            __import__("os").getenv(
                "COMPENSATION_WORKER_INTERVAL_SECONDS",
                "30",
            )
        ),
        batch_size=int(
            __import__("os").getenv(
                "COMPENSATION_WORKER_BATCH_SIZE",
                "50",
            )
        ),
    )
    app.state.idempotent_closure_executor = IdempotentClosureExecutor(
        effect_repository=RedisIdempotentEffectRepository(
            security_redis,
            prefix=__import__("os").getenv(
                "IDEMPOTENCY_PREFIX",
                "aslan:idempotency",
            ),
            ttl_seconds=int(
                __import__("os").getenv(
                    "IDEMPOTENCY_TTL_SECONDS",
                    "2592000",
                )
            ),
        ),
        compensation_repository=app.state.compensation_repository,
    )
    app.state.quorum_closure_service = (
        QuorumQuarantineClosureService(
            approval_repository=(
                app.state.quarantine_approval_repository
            ),
            quorum_repository=(
                app.state.quorum_approval_repository
            ),
            closure_service=(
                app.state.quarantine_closure_service
            ),
            execution_repository=(
                app.state.quorum_execution_repository
            ),
            heartbeat_interval_seconds=float(
                __import__("os").getenv(
                    "SESSION_MAINTENANCE_QUORUM_EXECUTION_HEARTBEAT_SECONDS",
                    "15",
                )
            ),
        )
    )

app.state.oidc_metadata_refresher = OidcMetadataRefresher(
    discovery_cache=app.state.oidc_discovery_cache,
    jwks_cache=app.state.oidc_jwks_cache,
    interval_seconds=float(
        __import__("os").getenv(
            "OIDC_REFRESH_INTERVAL_SECONDS",
            "60",
        )
    ),
)

if settings.environment == "test":
    app.state.rate_limiter = SlidingWindowRateLimiter(
        limit=1000,
        window_seconds=60,
    )
else:
    try:
        app.state.rate_limiter = (
            build_token_bucket_limiter()
        )
    except Exception:
        app.state.rate_limiter = (
            SlidingWindowRateLimiter(
                limit=120,
                window_seconds=60,
            )
        )

app.state.audit_repository = (
    build_audit_repository(
        settings.environment
    )
)

app.middleware("http")(maintenance_mode_middleware)
app.middleware("http")(drain_middleware)
app.middleware("http")(
    security_headers_middleware
)
app.middleware("http")(
    request_size_middleware
)

if (
    app.state.rate_limiter.__class__.__name__
    == "RedisTokenBucketRateLimiter"
):
    app.middleware("http")(
        token_bucket_middleware
    )
else:
    from .rate_limit import rate_limit_middleware
    app.middleware("http")(
        rate_limit_middleware
    )

app.middleware("http")(
    correlation_middleware
)

class ConnectionManager:
    def __init__(self):
        self.connections = {}

    async def connect(
        self,
        fixture_id,
        websocket,
    ):
        await websocket.accept()
        self.connections.setdefault(
            fixture_id,
            [],
        ).append(websocket)

    def disconnect(
        self,
        fixture_id,
        websocket,
    ):
        sockets = self.connections.get(
            fixture_id,
            [],
        )
        if websocket in sockets:
            sockets.remove(websocket)

    async def broadcast(
        self,
        fixture_id,
        payload,
    ):
        for websocket in list(
            self.connections.get(
                fixture_id,
                [],
            )
        ):
            try:
                await websocket.send_json(
                    payload
                )
            except Exception:
                self.disconnect(
                    fixture_id,
                    websocket,
                )

manager = ConnectionManager()
service = MatchStateService()
event_repository = build_event_repository()


def current_principal(request: Request):
    authorization = request.headers.get(
        "Authorization",
        "",
    )
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Bearer token gerekli",
        )
    token = authorization.removeprefix(
        "Bearer "
    ).strip()
    try:
        return request.app.state.identity_gateway.verify(
            token
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=401,
            detail=str(exc),
        ) from exc

def require_app_roles(*roles):
    def dependency(
        principal: UnifiedPrincipal = Depends(
            current_principal
        ),
    ):
        if not set(roles).intersection(
            principal.roles
        ):
            raise HTTPException(
                status_code=403,
                detail="Yetersiz rol",
            )
        return principal
    return dependency


@app.post("/admin/dr/checkpoints/{region}")
def save_dr_checkpoint(
    region: str,
    role: str = Query(pattern="^(PRIMARY|STANDBY)$"),
    epoch: int = Query(ge=0),
    replication_cursor: int = Query(ge=0),
    source_timestamp: int = Query(ge=0),
    applied_timestamp: int = Query(ge=0),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.dr_repository
    if repository is None:
        raise HTTPException(
            status_code=409,
            detail="DR repository etkin değil",
        )
    item = repository.save_checkpoint(
        region=region,
        role=role,
        epoch=epoch,
        replication_cursor=replication_cursor,
        source_timestamp=source_timestamp,
        applied_timestamp=applied_timestamp,
    )
    return item.__dict__

@app.post("/admin/dr/promote/{region}")
def promote_dr_region(
    region: str,
    expected_epoch: int = Query(ge=0),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    repository = app.state.dr_repository
    if repository is None:
        raise HTTPException(
            status_code=409,
            detail="DR repository etkin değil",
        )
    try:
        result = repository.promote(
            region=region,
            expected_epoch=expected_epoch,
        )
    except PromotionRejected as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except SplitBrainRisk as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    metrics.increment("aslan_dr_promotions_total")
    return result.__dict__

@app.get("/admin/dr/health")
def get_dr_health(
    region: str | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.dr_repository
    coordinator = app.state.dr_coordinator
    if repository is None or coordinator is None:
        return {"enabled": False}

    payload = {
        "enabled": True,
        "topology": repository.health(),
    }
    if region:
        payload["objective"] = coordinator.evaluate(
            region
        ).__dict__
    return payload


@app.post("/admin/self-healing/nodes/{node_id}/report")
def report_node_health(
    node_id: str,
    region: str = Query(min_length=1),
    role: str = Query(min_length=1),
    cpu_percent: float = Query(ge=0, le=100),
    memory_percent: float = Query(ge=0, le=100),
    error_rate: float = Query(ge=0, le=1),
    latency_ms: float = Query(ge=0),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    orchestrator = app.state.self_healing_orchestrator
    if orchestrator is None:
        raise HTTPException(
            status_code=409,
            detail="Self-healing etkin değil",
        )
    return orchestrator.report(
        node_id=node_id,
        region=region,
        role=role,
        cpu_percent=cpu_percent,
        memory_percent=memory_percent,
        error_rate=error_rate,
        latency_ms=latency_ms,
    ).__dict__

@app.post("/admin/self-healing/reconcile")
async def reconcile_self_healing(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.self_healing_worker
    if worker is None:
        raise HTTPException(
            status_code=409,
            detail="Self-healing worker etkin değil",
        )
    actions = await worker.run_once()
    metrics.increment("aslan_self_healing_cycles_total")
    if actions:
        metrics.increment(
            "aslan_self_healing_actions_total",
            len(actions),
        )
    return {"items": [item.__dict__ for item in actions]}

@app.get("/admin/self-healing/health")
def get_self_healing_health(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    orchestrator = app.state.self_healing_orchestrator
    if orchestrator is None:
        return {"enabled": False}
    return {"enabled": True, **orchestrator.cluster_health()}

@app.get("/admin/self-healing/actions")
def list_self_healing_actions(
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    orchestrator = app.state.self_healing_orchestrator
    if orchestrator is None:
        return {"enabled": False, "items": []}
    return {
        "enabled": True,
        "items": [
            item.__dict__
            for item in orchestrator.repository.list_actions(limit=limit)
        ],
    }

@app.get("/live")
def liveness():
    return {"live": True, "version": app.version}

@app.post("/admin/upgrade/drain")
def enter_drain_mode(
    reason: str = Query(min_length=3, max_length=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    state = app.state.drain_controller.enter(reason=reason)
    metrics.increment("aslan_upgrade_drain_entries_total")
    return state.__dict__

@app.post("/admin/upgrade/resume")
def exit_drain_mode(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    state = app.state.drain_controller.exit()
    metrics.increment("aslan_upgrade_drain_exits_total")
    return state.__dict__

@app.get("/admin/upgrade/drain")
def get_drain_mode(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return app.state.drain_controller.snapshot().__dict__

@app.post("/admin/upgrade/{rollout_id}/start")
def start_rolling_upgrade(
    rollout_id: str,
    source_version: str = Query(min_length=1),
    target_version: str = Query(min_length=1),
    schema_compatible: bool = Query(default=True),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    try:
        state = app.state.rolling_upgrade_coordinator.start(
            rollout_id=rollout_id,
            source_version=source_version,
            target_version=target_version,
            schema_compatible=schema_compatible,
        )
    except (IncompatibleRelease, UpgradeConflict) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    metrics.increment("aslan_rolling_upgrade_started_total")
    return state.__dict__

@app.post("/admin/upgrade/{rollout_id}/advance")
def advance_rolling_upgrade(
    rollout_id: str,
    health_ok: bool = Query(default=True),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        state = app.state.rolling_upgrade_coordinator.advance(
            rollout_id,
            health_ok=health_ok,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpgradeConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    metrics.increment(
        "aslan_rolling_upgrade_rollbacks_total"
        if state.status == "ROLLED_BACK"
        else "aslan_rolling_upgrade_advances_total"
    )
    return state.__dict__

@app.post("/admin/upgrade/{rollout_id}/rollback")
def rollback_rolling_upgrade(
    rollout_id: str,
    reason: str = Query(min_length=3, max_length=1000),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    try:
        state = app.state.rolling_upgrade_coordinator.rollback(
            rollout_id,
            reason=reason,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except UpgradeConflict as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    metrics.increment("aslan_rolling_upgrade_rollbacks_total")
    return state.__dict__

@app.get("/admin/upgrade/{rollout_id}")
def get_rolling_upgrade(
    rollout_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    state = app.state.rolling_upgrade_coordinator.status(rollout_id)
    if state is None:
        raise HTTPException(
            status_code=404,
            detail="Rolling upgrade kaydı bulunamadı",
        )
    return state.__dict__


@app.post("/admin/production-readiness/maintenance/enable")
def enable_maintenance_mode(
    reason: str = Query(min_length=3, max_length=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    state = app.state.maintenance_controller.enable(
        reason=reason,
        owner=principal.subject,
    )
    metrics.increment(
        "aslan_maintenance_mode_entries_total"
    )
    return state.__dict__

@app.post("/admin/production-readiness/maintenance/disable")
def disable_maintenance_mode(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    state = app.state.maintenance_controller.disable()
    metrics.increment(
        "aslan_maintenance_mode_exits_total"
    )
    return state.__dict__

@app.get("/admin/production-readiness/maintenance")
def get_maintenance_mode(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return app.state.maintenance_controller.snapshot().__dict__

@app.get("/admin/production-readiness/report")
def production_readiness_report(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    certification = app.state.operational_certification
    if certification is None:
        raise HTTPException(
            status_code=409,
            detail="Production readiness etkin değil",
        )
    report = certification.generate()
    metrics.increment(
        "aslan_production_readiness_reports_total"
    )
    return report


@app.get("/admin/release/manifest")
def get_release_manifest(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    builder = app.state.release_manifest_builder
    components = (
        ReleaseComponent(
            name="api",
            version=app.version,
            artifact_sha256=(
                "a" * 64
            ),
            critical=True,
        ),
        ReleaseComponent(
            name="worker",
            version=app.version,
            artifact_sha256=(
                "b" * 64
            ),
            critical=True,
        ),
        ReleaseComponent(
            name="football-core",
            version=app.version,
            artifact_sha256=(
                "c" * 64
            ),
            critical=True,
        ),
    )
    manifest = builder.build(
        release_id="aslan-11.0.0-rc.1",
        version=app.version,
        channel="rc",
        build_id=__import__("os").getenv(
            "BUILD_ID",
            "local-build",
        ),
        source_revision=__import__("os").getenv(
            "SOURCE_REVISION",
            "unknown",
        ),
        schema_version=__import__("os").getenv(
            "SCHEMA_VERSION",
            "11.0",
        ),
        minimum_rollback_version="10.48.0",
        components=components,
    )
    return {
        **manifest.__dict__,
        "components": [
            item.__dict__
            for item in manifest.components
        ],
    }

@app.get("/admin/release/certification")
def get_release_certification(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    builder = app.state.release_manifest_builder
    manifest = builder.build(
        release_id="aslan-11.0.0-rc.1",
        version=app.version,
        channel="rc",
        build_id=__import__("os").getenv(
            "BUILD_ID",
            "local-build",
        ),
        source_revision=__import__("os").getenv(
            "SOURCE_REVISION",
            "unknown",
        ),
        schema_version=__import__("os").getenv(
            "SCHEMA_VERSION",
            "11.0",
        ),
        minimum_rollback_version="10.48.0",
        components=(
            ReleaseComponent(
                name="api",
                version=app.version,
                artifact_sha256="a" * 64,
                critical=True,
            ),
            ReleaseComponent(
                name="worker",
                version=app.version,
                artifact_sha256="b" * 64,
                critical=True,
            ),
        ),
    )
    return app.state.release_certification.certify(
        manifest
    )

@app.get("/admin/release/sbom")
def get_release_sbom(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return app.state.sbom_builder.build(
        document_name="aslan-platform",
        version=app.version,
        components=(
            SoftwareComponent(
                name="fastapi",
                version="runtime",
                license="MIT",
                source="python-package",
                sha256="d" * 64,
            ),
            SoftwareComponent(
                name="redis",
                version="runtime",
                license="MIT",
                source="python-package",
                sha256="e" * 64,
            ),
            SoftwareComponent(
                name="sqlalchemy",
                version="runtime",
                license="MIT",
                source="python-package",
                sha256="f" * 64,
            ),
        ),
    )


@app.post("/admin/providers/events/normalize")
def normalize_provider_event(
    provider: str,
    provider_event_id: str,
    match_id: str,
    event_type: str,
    occurred_at: int = Query(ge=1),
    team_id: str | None = None,
    player_id: str | None = None,
    value: float | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    gateway = app.state.provider_gateway
    if gateway is None:
        raise HTTPException(
            status_code=409,
            detail="Provider gateway etkin değil",
        )

    try:
        event = gateway.ingest(
            RawProviderEvent(
                provider=provider,
                provider_event_id=provider_event_id,
                match_id=match_id,
                event_type=event_type,
                occurred_at=occurred_at,
                payload={
                    "team_id": team_id,
                    "player_id": player_id,
                    "value": value,
                },
                received_at=int(__import__("time").time()),
            )
        )
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_provider_events_normalized_total"
    )
    return event.__dict__

@app.get("/admin/providers/{provider}/trust")
def get_provider_trust(
    provider: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    gateway = app.state.provider_gateway
    if gateway is None:
        raise HTTPException(
            status_code=409,
            detail="Provider gateway etkin değil",
        )
    return (
        gateway.quality_engine.repository
        .get(provider).__dict__
    )

@app.get("/admin/providers/confidence/adjust")
def adjust_prediction_confidence(
    base_confidence: float = Query(ge=0, le=1),
    provider_trust: int = Query(ge=0, le=100),
    data_quality: int = Query(ge=0, le=100),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return (
        app.state.prediction_confidence_adjuster
        .adjust(
            base_confidence=base_confidence,
            provider_trust=provider_trust,
            data_quality=data_quality,
        ).__dict__
    )


@app.post("/admin/models/register")
def register_model(
    model_id: str,
    name: str,
    version: str,
    framework: str,
    artifact_uri: str,
    artifact_sha256: str,
    feature_version: str,
    training_dataset: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    try:
        model = app.state.model_registry.register(
            model_id=model_id,
            name=name,
            version=version,
            framework=framework,
            artifact_uri=artifact_uri,
            artifact_sha256=artifact_sha256,
            feature_version=feature_version,
            training_dataset=training_dataset,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment("aslan_models_registered_total")
    return model.__dict__

@app.get("/admin/models")
def list_models(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in app.state.model_registry.list_models()
        ]
    }

@app.post("/admin/models/{slot}/champion/{model_id}")
def assign_model_champion(
    slot: str,
    model_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    try:
        state = (
            app.state.model_deployment_manager
            .assign_champion(
                slot=slot,
                model_id=model_id,
            )
        )
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_model_champion_assignments_total"
    )
    return state.__dict__

@app.post("/admin/models/{slot}/challenger/{model_id}")
def start_model_challenger(
    slot: str,
    model_id: str,
    rollout_percent: int = Query(default=5, ge=1, le=50),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    try:
        state = (
            app.state.model_deployment_manager
            .start_challenger(
                slot=slot,
                model_id=model_id,
                rollout_percent=rollout_percent,
            )
        )
    except (KeyError, RuntimeError, ValueError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_model_challenger_started_total"
    )
    return state.__dict__

@app.post("/admin/models/{slot}/promote")
def promote_model_challenger(
    slot: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    try:
        state = (
            app.state.model_deployment_manager
            .promote_challenger(slot=slot)
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_model_challenger_promotions_total"
    )
    return state.__dict__

@app.post("/admin/models/{slot}/rollback")
def rollback_model(
    slot: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    try:
        state = (
            app.state.model_deployment_manager
            .rollback(slot=slot)
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_model_rollbacks_total"
    )
    return state.__dict__

@app.get("/admin/models/{slot}/deployment")
def get_model_deployment(
    slot: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    return (
        app.state.model_deployment_manager
        .get(slot).__dict__
    )

@app.get("/admin/models/calibrate")
def calibrate_probability(
    probability: float = Query(ge=0, le=1),
    slope: float = Query(default=1.0),
    intercept: float = Query(default=0.0),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    calibrator = ProbabilityCalibrator(
        slope=slope,
        intercept=intercept,
    )
    return {
        "input": probability,
        "calibrated": calibrator.calibrate(
            probability
        ),
    }


@app.post("/admin/model-monitoring/{model_id}/health")
def update_model_health(
    model_id: str,
    probabilities: str,
    outcomes: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    try:
        probability_values = tuple(
            float(item)
            for item in probabilities.split(",")
            if item.strip()
        )
        outcome_values = tuple(
            int(item)
            for item in outcomes.split(",")
            if item.strip()
        )
        snapshot = (
            app.state.model_monitoring_service
            .update_health(
                model_id=model_id,
                probabilities=probability_values,
                outcomes=outcome_values,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_model_health_updates_total"
    )
    return snapshot.__dict__

@app.get("/admin/model-monitoring/{model_id}/health")
def get_model_health(
    model_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    snapshot = (
        app.state.model_monitoring_service
        .repository.get_health(model_id)
    )
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="Model health kaydı bulunamadı",
        )
    return snapshot.__dict__

@app.post("/admin/model-monitoring/{model_id}/prediction-drift")
def detect_prediction_drift(
    model_id: str,
    baseline: str,
    current: str,
    threshold: float = Query(default=0.2, ge=0),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    try:
        signal = (
            app.state.model_monitoring_service
            .detect_prediction_drift(
                model_id=model_id,
                baseline=tuple(
                    float(item)
                    for item in baseline.split(",")
                    if item.strip()
                ),
                current=tuple(
                    float(item)
                    for item in current.split(",")
                    if item.strip()
                ),
                threshold=threshold,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_prediction_drift_checks_total"
    )
    return signal.__dict__

@app.post("/admin/model-monitoring/{model_id}/feature-drift")
def detect_feature_drift(
    model_id: str,
    feature_name: str,
    baseline: str,
    current: str,
    threshold: float = Query(default=1.0, ge=0),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    try:
        signal = (
            app.state.model_monitoring_service
            .detect_feature_drift(
                model_id=model_id,
                feature_name=feature_name,
                baseline=tuple(
                    float(item)
                    for item in baseline.split(",")
                    if item.strip()
                ),
                current=tuple(
                    float(item)
                    for item in current.split(",")
                    if item.strip()
                ),
                threshold=threshold,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_feature_drift_checks_total"
    )
    return signal.__dict__

@app.get("/admin/model-monitoring/{model_id}/signals")
def list_model_drift_signals(
    model_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.model_monitoring_service
                .repository.list_signals(
                    model_id,
                    limit=limit,
                )
            )
        ]
    }

@app.get("/admin/model-monitoring/reviews")
def list_model_reviews(
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.model_monitoring_service
                .repository.list_reviews(
                    status=status,
                    limit=limit,
                )
            )
        ]
    }

@app.get("/admin/model-monitoring/shadow-compare")
def shadow_compare(
    champion: str,
    shadow: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    try:
        return (
            app.state.model_monitoring_service
            .shadow_compare(
                champion_probabilities=tuple(
                    float(item)
                    for item in champion.split(",")
                    if item.strip()
                ),
                shadow_probabilities=tuple(
                    float(item)
                    for item in shadow.split(",")
                    if item.strip()
                ),
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.post("/admin/features/register")
def register_feature(
    name: str,
    version: str,
    entity_type: str,
    value_type: str,
    owner: str,
    ttl_seconds: int = Query(ge=1),
    max_age_seconds: int = Query(ge=1),
    status: str = Query(default="PRODUCTION"),
    source: str = Query(min_length=1),
    transformation: str = Query(min_length=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops")
    ),
):
    current = int(__import__("time").time())
    definition = FeatureDefinition(
        name=name,
        version=version,
        entity_type=entity_type,
        value_type=value_type,
        owner=owner,
        ttl_seconds=ttl_seconds,
        max_age_seconds=max_age_seconds,
        status=status,
        source=source,
        transformation=transformation,
        created_at=current,
        updated_at=current,
    )
    try:
        saved = app.state.feature_store.register_definition(
            definition
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_feature_definitions_registered_total"
    )
    return saved.__dict__

@app.get("/admin/features")
def list_features(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.feature_store
                .list_definitions()
            )
        ]
    }

@app.post("/admin/features/{feature_name}/{feature_version}/values")
def put_feature_value(
    feature_name: str,
    feature_version: str,
    tenant_id: str,
    entity_id: str,
    event_time: int = Query(ge=1),
    value: str = Query(min_length=1),
    source: str = Query(min_length=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    definition = app.state.feature_store.get_definition(
        feature_name,
        feature_version,
    )
    if definition is None:
        raise HTTPException(
            status_code=404,
            detail="Feature definition bulunamadı",
        )

    parsed_value = value
    try:
        if definition.value_type.upper() == "FLOAT":
            parsed_value = float(value)
        elif definition.value_type.upper() == "INT":
            parsed_value = int(value)
        elif definition.value_type.upper() == "BOOL":
            parsed_value = value.lower() in {
                "1",
                "true",
                "yes",
            }
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="Feature değeri parse edilemedi",
        ) from exc

    ingested_at = int(__import__("time").time())
    item = FeatureValue(
        tenant_id=tenant_id,
        entity_id=entity_id,
        feature_name=feature_name,
        feature_version=feature_version,
        value=parsed_value,
        event_time=event_time,
        ingested_at=ingested_at,
        expires_at=(
            ingested_at + definition.ttl_seconds
        ),
        source=source,
    )
    try:
        saved = app.state.feature_store.put(item)
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_feature_values_written_total"
    )
    return saved.__dict__

@app.get("/admin/features/{feature_name}/{feature_version}/online")
def get_online_feature(
    feature_name: str,
    feature_version: str,
    tenant_id: str,
    entity_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    item = app.state.feature_store.get_online(
        tenant_id=tenant_id,
        entity_id=entity_id,
        feature_name=feature_name,
        feature_version=feature_version,
    )
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Online feature değeri bulunamadı",
        )
    return item.__dict__

@app.get("/admin/features/{feature_name}/{feature_version}/as-of")
def get_feature_as_of(
    feature_name: str,
    feature_version: str,
    tenant_id: str,
    entity_id: str,
    as_of: int = Query(ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    item = app.state.feature_store.get_as_of(
        tenant_id=tenant_id,
        entity_id=entity_id,
        feature_name=feature_name,
        feature_version=feature_version,
        as_of=as_of,
    )
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Point-in-time feature bulunamadı",
        )
    return item.__dict__

@app.get("/admin/features/{feature_name}/{feature_version}/freshness")
def get_feature_freshness(
    feature_name: str,
    feature_version: str,
    tenant_id: str,
    entity_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    try:
        freshness = app.state.feature_store.freshness(
            tenant_id=tenant_id,
            entity_id=entity_id,
            feature_name=feature_name,
            feature_version=feature_version,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return freshness.__dict__

@app.get("/admin/features/{feature_name}/{feature_version}/lineage")
def get_feature_lineage(
    feature_name: str,
    feature_version: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    try:
        return (
            app.state.feature_lineage_service
            .describe(
                feature_name=feature_name,
                feature_version=feature_version,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@app.post("/admin/inference/runtime/{model_id}/warmup")
async def warmup_model_runtime(
    model_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    try:
        state = await (
            app.state.model_runtime_registry
            .warmup(model_id)
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_model_warmups_total"
    )
    return state.__dict__

@app.get("/admin/inference/runtime/{model_id}/status")
def get_model_runtime_status(
    model_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    try:
        return (
            app.state.model_runtime_registry
            .status(model_id).__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.post("/admin/inference/{slot}")
async def run_inference(
    slot: str,
    tenant_id: str,
    entity_id: str,
    features: str,
    explain: bool = Query(default=False),
    latency_class: str = Query(default="REALTIME"),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "mlops", "ops")
    ),
):
    try:
        parsed_features = __import__("json").loads(
            features
        )
        if not isinstance(parsed_features, dict):
            raise ValueError(
                "features JSON object olmalıdır"
            )
        request = InferenceRequest(
            request_id=__import__("uuid").uuid4().hex,
            tenant_id=tenant_id,
            slot=slot,
            entity_id=entity_id,
            features=parsed_features,
            explain=explain,
            latency_class=latency_class,
        )
        result = await app.state.inference_service.infer(
            request
        )
    except (
        ValueError,
        RuntimeError,
        KeyError,
    ) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_inference_requests_total"
    )
    if result.cached:
        metrics.increment(
            "aslan_inference_cache_hits_total"
        )
    if result.fallback_used:
        metrics.increment(
            "aslan_inference_fallbacks_total"
        )
    return result.__dict__


@app.post("/admin/streaming/events")
def process_streaming_event(
    match_id: str,
    event_id: str,
    event_type: str,
    minute: int = Query(ge=0, le=130),
    event_time: int = Query(ge=1),
    xg: float = Query(default=0.0, ge=0),
    source: str = Query(min_length=1),
    team_id: str | None = None,
    player_id: str | None = None,
    value: float | None = None,
    home_team_id: str | None = None,
    away_team_id: str | None = None,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "mlops")),
):
    try:
        snapshot, decisions = app.state.streaming_analytics_engine.process(
            LiveMatchEvent(
                match_id=match_id, event_id=event_id, event_type=event_type.upper(),
                team_id=team_id, player_id=player_id, minute=minute,
                event_time=event_time, xg=xg, value=value, source=source,
            ),
            home_team_id=home_team_id, away_team_id=away_team_id,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    metrics.increment("aslan_streaming_events_processed_total")
    if decisions:
        metrics.increment("aslan_streaming_decisions_total", len(decisions))
    return {"snapshot": snapshot.__dict__, "decisions": [d.__dict__ for d in decisions]}

@app.get("/admin/streaming/{match_id}/snapshot")
def get_streaming_snapshot(
    match_id: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "mlops")),
):
    snapshot = app.state.streaming_analytics_engine.repository.get_snapshot(match_id)
    if snapshot is None:
        raise HTTPException(status_code=404, detail="Streaming snapshot bulunamadı")
    return snapshot.__dict__

@app.get("/admin/streaming/{match_id}/decisions")
def list_streaming_decisions(
    match_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "mlops")),
):
    return {"items": [d.__dict__ for d in app.state.streaming_analytics_engine.repository.list_decisions(match_id, limit=limit)]}


@app.post("/admin/live-decisions/{match_id}/execute")
async def execute_live_decision(
    match_id: str,
    trigger: str,
    event_time: int = Query(ge=1),
    slot: str = Query(min_length=1),
    tenant_id: str = Query(min_length=1),
    explain: bool = Query(default=True),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops", "mlops")
    ),
):
    snapshot = (
        app.state.streaming_analytics_engine
        .repository.get_snapshot(match_id)
    )
    if snapshot is None:
        raise HTTPException(
            status_code=404,
            detail="Streaming snapshot bulunamadı",
        )

    features = (
        app.state.live_decision_orchestrator
        .snapshot_from_streaming(snapshot)
    )

    try:
        record = await (
            app.state.live_decision_orchestrator
            .execute(
                match_id=match_id,
                trigger=trigger,
                event_time=event_time,
                slot=slot,
                tenant_id=tenant_id,
                feature_snapshot=features,
                explain=explain,
            )
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_live_decisions_total"
    )
    if record.fallback_used:
        metrics.increment(
            "aslan_live_decision_fallbacks_total"
        )
    return record.__dict__

@app.get("/admin/live-decisions/{match_id}")
def list_live_decisions(
    match_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops", "mlops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.live_decision_orchestrator
                .repository.list_records(
                    match_id,
                    limit=limit,
                )
            )
        ]
    }


@app.post("/admin/alerts/subscriptions")
def create_alert_subscription(
    tenant_id: str,
    destination: str,
    minimum_severity: str = Query(default="MEDIUM"),
    match_id: str | None = None,
    trigger: str | None = None,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops")),
):
    current = int(__import__("time").time())
    subscription_id = __import__("hashlib").sha256(
        f"{tenant_id}|{destination}|{match_id}|{trigger}|{current}".encode()
    ).hexdigest()
    item = AlertSubscription(
        subscription_id, tenant_id, match_id, trigger,
        minimum_severity.upper(), destination, True, current
    )
    app.state.alert_repository.save_subscription(item)
    metrics.increment("aslan_alert_subscriptions_total")
    return item.__dict__

@app.get("/admin/alerts/subscriptions/{tenant_id}")
def list_alert_subscriptions(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops")),
):
    return {"items":[x.__dict__ for x in app.state.alert_repository.list_subscriptions(tenant_id)]}

@app.post("/admin/alerts/publish")
async def publish_alert(
    tenant_id: str,
    match_id: str,
    trigger: str,
    severity: str,
    title: str,
    body: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops")),
):
    current = int(__import__("time").time())
    alert_id = __import__("hashlib").sha256(
        f"{tenant_id}|{match_id}|{trigger}|{current}".encode()
    ).hexdigest()
    result = await app.state.alert_delivery_service.publish(
        AlertMessage(
            alert_id, tenant_id, match_id, trigger, severity.upper(),
            title, body, {}, current
        )
    )
    metrics.increment("aslan_alerts_published_total")
    return result

@app.get("/admin/alerts/{alert_id}/attempts")
def list_alert_attempts(
    alert_id: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops")),
):
    return {"items":[x.__dict__ for x in app.state.alert_repository.list_attempts(alert_id)]}

@app.get("/admin/alerts/dead-letter")
def list_alert_dead_letters(
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops")),
):
    return {"items":list(app.state.alert_repository.list_dead_letters(limit=limit))}


@app.post("/admin/alert-policies")
def create_alert_policy(
    tenant_id: str,
    minimum_severity: str,
    dedup_window_seconds: int = Query(ge=1),
    acknowledge_sla_seconds: int = Query(ge=1),
    escalation_target: str = Query(min_length=1),
    trigger: str | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    current = int(__import__("time").time())
    policy_id = __import__("hashlib").sha256(
        (
            f"{tenant_id}|{trigger}|"
            f"{minimum_severity}|{current}"
        ).encode("utf-8")
    ).hexdigest()

    policy = AlertPolicy(
        policy_id=policy_id,
        tenant_id=tenant_id,
        trigger=trigger,
        minimum_severity=minimum_severity.upper(),
        dedup_window_seconds=dedup_window_seconds,
        acknowledge_sla_seconds=acknowledge_sla_seconds,
        escalation_target=escalation_target,
        enabled=True,
        created_at=current,
    )
    app.state.alert_policy_repository.save_policy(
        policy
    )
    return policy.__dict__

@app.get("/admin/alert-policies/{tenant_id}")
def list_alert_policies(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.alert_policy_repository
                .list_policies(tenant_id)
            )
        ]
    }

@app.post("/admin/alert-policies/silences")
def create_alert_silence(
    tenant_id: str,
    starts_at: int = Query(ge=1),
    ends_at: int = Query(ge=1),
    reason: str = Query(min_length=3),
    match_id: str | None = None,
    trigger: str | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    if ends_at <= starts_at:
        raise HTTPException(
            status_code=422,
            detail="ends_at starts_at değerinden büyük olmalıdır",
        )

    silence_id = __import__("hashlib").sha256(
        (
            f"{tenant_id}|{match_id}|"
            f"{trigger}|{starts_at}|{ends_at}"
        ).encode("utf-8")
    ).hexdigest()

    silence = SilenceRule(
        silence_id=silence_id,
        tenant_id=tenant_id,
        match_id=match_id,
        trigger=trigger,
        starts_at=starts_at,
        ends_at=ends_at,
        reason=reason,
        created_by=principal.subject,
    )
    app.state.alert_policy_repository.save_silence(
        silence
    )
    return silence.__dict__

@app.post("/admin/alert-incidents/open")
def open_alert_incident(
    alert_id: str,
    tenant_id: str,
    match_id: str,
    trigger: str,
    severity: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    incident = (
        app.state.alert_incident_service
        .open_incident(
            alert_id=alert_id,
            tenant_id=tenant_id,
            match_id=match_id,
            trigger=trigger,
            severity=severity.upper(),
        )
    )
    return {
        "created": incident is not None,
        "incident": (
            incident.__dict__
            if incident is not None
            else None
        ),
    }

@app.post("/admin/alert-incidents/{incident_id}/acknowledge")
def acknowledge_alert_incident(
    incident_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        incident = (
            app.state.alert_incident_service
            .acknowledge(
                incident_id=incident_id,
                owner=principal.subject,
            )
        )
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    return incident.__dict__

@app.post("/admin/alert-incidents/{incident_id}/resolve")
def resolve_alert_incident(
    incident_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        incident = (
            app.state.alert_incident_service
            .resolve(
                incident_id=incident_id,
                owner=principal.subject,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return incident.__dict__

@app.post("/admin/alert-incidents/{tenant_id}/escalate")
def escalate_alert_incidents(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    items = (
        app.state.alert_incident_service
        .escalate_due(tenant_id=tenant_id)
    )
    return {
        "items": [
            item.__dict__
            for item in items
        ]
    }

@app.get("/admin/alert-incidents/{tenant_id}")
def list_alert_incidents(
    tenant_id: str,
    status: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.alert_policy_repository
                .list_incidents(
                    tenant_id,
                    status=status,
                    limit=limit,
                )
            )
        ]
    }


@app.post("/admin/postmortems/from-incident/{incident_id}")
def create_postmortem(
    incident_id: str,
    title: str = Query(min_length=3),
    summary: str = Query(min_length=3),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        item = app.state.postmortem_service.create_from_incident(
            incident_id=incident_id,
            title=title,
            summary=summary,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return item.__dict__

@app.post("/admin/postmortems/{postmortem_id}/analysis")
def update_postmortem_analysis(
    postmortem_id: str,
    root_cause: str = Query(min_length=3),
    impact: str = Query(min_length=3),
    lessons: str = Query(default=""),
    contributing_factors: str = Query(default=""),
    expected_revision: int = Query(ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        item = app.state.postmortem_service.update_analysis(
            postmortem_id=postmortem_id,
            root_cause=root_cause,
            impact=impact,
            lessons=lessons,
            contributing_factors=tuple(
                value.strip()
                for value in contributing_factors.split(",")
                if value.strip()
            ),
            expected_revision=expected_revision,
        )
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    return item.__dict__

@app.post("/admin/postmortems/{postmortem_id}/evidence")
def add_postmortem_evidence(
    postmortem_id: str,
    kind: str = Query(min_length=2),
    summary: str = Query(min_length=3),
    expected_revision: int = Query(ge=1),
    reference: str | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        item = app.state.postmortem_service.add_evidence(
            postmortem_id=postmortem_id,
            kind=kind,
            summary=summary,
            reference=reference,
            expected_revision=expected_revision,
        )
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    return item.__dict__

@app.post("/admin/postmortems/{postmortem_id}/actions")
def add_postmortem_action(
    postmortem_id: str,
    title: str = Query(min_length=3),
    owner: str = Query(min_length=1),
    expected_revision: int = Query(ge=1),
    due_at: int | None = Query(default=None, ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        item = app.state.postmortem_service.add_action(
            postmortem_id=postmortem_id,
            title=title,
            owner=owner,
            due_at=due_at,
            expected_revision=expected_revision,
        )
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    return item.__dict__

@app.post(
    "/admin/postmortems/{postmortem_id}/actions/"
    "{action_id}/complete"
)
def complete_postmortem_action(
    postmortem_id: str,
    action_id: str,
    expected_revision: int = Query(ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        item = app.state.postmortem_service.complete_action(
            postmortem_id=postmortem_id,
            action_id=action_id,
            expected_revision=expected_revision,
        )
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    return item.__dict__

@app.post("/admin/postmortems/{postmortem_id}/publish")
def publish_postmortem(
    postmortem_id: str,
    expected_revision: int = Query(ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        item = app.state.postmortem_service.publish(
            postmortem_id=postmortem_id,
            expected_revision=expected_revision,
        )
    except (KeyError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_postmortems_published_total"
    )
    return item.__dict__

@app.get("/admin/postmortems/{tenant_id}/search")
def search_postmortems(
    tenant_id: str,
    query: str = Query(min_length=3),
    limit: int = Query(default=5, ge=1, le=20),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return {
        "items": [
            {
                "score": score,
                "postmortem": item.__dict__,
            }
            for item, score in (
                app.state.postmortem_repository
                .search_similar(
                    tenant_id=tenant_id,
                    query=query,
                    limit=limit,
                )
            )
        ]
    }

@app.get("/admin/postmortems/{postmortem_id}")
def get_postmortem(
    postmortem_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    item = app.state.postmortem_repository.get(
        postmortem_id
    )
    if item is None:
        raise HTTPException(
            status_code=404,
            detail="Postmortem bulunamadı",
        )
    return item.__dict__


@app.post("/admin/reliability/slos")
def create_reliability_slo(
    slo_id: str,
    tenant_id: str,
    service: str,
    indicator: str,
    target: float = Query(gt=0, lt=1),
    window_seconds: int = Query(ge=60),
    warning_burn_rate: float = Query(default=1.0, gt=0),
    critical_burn_rate: float = Query(default=2.0, gt=0),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        slo = app.state.reliability_service.create_slo(
            slo_id=slo_id,
            tenant_id=tenant_id,
            service=service,
            indicator=indicator,
            target=target,
            window_seconds=window_seconds,
            warning_burn_rate=warning_burn_rate,
            critical_burn_rate=critical_burn_rate,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    metrics.increment("aslan_reliability_slos_total")
    return slo.__dict__

@app.post("/admin/reliability/slos/{slo_id}/observations")
def record_reliability_observation(
    slo_id: str,
    observation_id: str,
    good_events: int = Query(ge=0),
    total_events: int = Query(ge=1),
    observed_at: int | None = Query(default=None, ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        observation = app.state.reliability_service.record(
            observation_id=observation_id,
            slo_id=slo_id,
            good_events=good_events,
            total_events=total_events,
            observed_at=observed_at,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_reliability_observations_total"
    )
    return observation.__dict__

@app.get("/admin/reliability/slos/{slo_id}/budget")
def get_reliability_error_budget(
    slo_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        return (
            app.state.reliability_service
            .calculate(slo_id=slo_id).__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.get("/admin/reliability/{tenant_id}/score")
def get_tenant_reliability_score(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return (
        app.state.reliability_service
        .reliability_score(tenant_id=tenant_id)
    )

@app.get("/admin/reliability/{tenant_id}/slos")
def list_tenant_slos(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.reliability_service
                .repository.list_slos(tenant_id)
            )
        ]
    }


@app.post("/admin/release-guard/policies")
def create_release_guard_policy(
    policy_id: str,
    tenant_id: str,
    minimum_reliability_score: int = Query(
        default=70,
        ge=0,
        le=100,
    ),
    block_on_warning: bool = Query(default=False),
    block_on_critical: bool = Query(default=True),
    require_override_reason: bool = Query(default=True),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        policy = (
            app.state.release_guard_service
            .create_policy(
                policy_id=policy_id,
                tenant_id=tenant_id,
                minimum_reliability_score=(
                    minimum_reliability_score
                ),
                block_on_warning=block_on_warning,
                block_on_critical=block_on_critical,
                require_override_reason=(
                    require_override_reason
                ),
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_release_guard_policies_total"
    )
    return policy.__dict__

@app.post("/admin/release-guard/{tenant_id}/evaluate")
def evaluate_release_guard(
    tenant_id: str,
    decision_id: str,
    release_id: str,
    override: bool = Query(default=False),
    override_reason: str | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        decision = (
            app.state.release_guard_service
            .evaluate(
                decision_id=decision_id,
                tenant_id=tenant_id,
                release_id=release_id,
                override_actor=(
                    principal.subject
                    if override
                    else None
                ),
                override_reason=(
                    override_reason
                    if override
                    else None
                ),
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_release_guard_evaluations_total"
    )
    if not decision.allowed:
        metrics.increment(
            "aslan_release_guard_blocks_total"
        )
    if decision.overridden:
        metrics.increment(
            "aslan_release_guard_overrides_total"
        )
    return decision.__dict__

@app.get("/admin/release-guard/{tenant_id}/decisions")
def list_release_guard_decisions(
    tenant_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.release_guard_service
                .repository.list_decisions(
                    tenant_id,
                    limit=limit,
                )
            )
        ]
    }


@app.post("/admin/progressive-delivery/plans")
def create_progressive_delivery_plan(
    plan_id: str,
    tenant_id: str,
    release_id: str,
    stages: str = Query(default="5,25,50,100"),
    minimum_reliability_score: int = Query(
        default=70,
        ge=0,
        le=100,
    ),
    max_warning_slos: int = Query(
        default=0,
        ge=0,
    ),
    max_critical_slos: int = Query(
        default=0,
        ge=0,
    ),
    observation_window_seconds: int = Query(
        default=300,
        ge=30,
    ),
    auto_rollback: bool = Query(default=True),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        parsed_stages = tuple(
            int(item.strip())
            for item in stages.split(",")
            if item.strip()
        )
        plan = (
            app.state.progressive_delivery_service
            .create_plan(
                plan_id=plan_id,
                tenant_id=tenant_id,
                release_id=release_id,
                stages=parsed_stages,
                minimum_reliability_score=(
                    minimum_reliability_score
                ),
                max_warning_slos=max_warning_slos,
                max_critical_slos=max_critical_slos,
                observation_window_seconds=(
                    observation_window_seconds
                ),
                auto_rollback=auto_rollback,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_progressive_delivery_plans_total"
    )
    return {
        **plan.__dict__,
        "stages": list(plan.stages),
    }

@app.post("/admin/progressive-delivery/{plan_id}/start")
def start_progressive_delivery(
    plan_id: str,
    gate_decision_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        state = (
            app.state.progressive_delivery_service
            .start(
                plan_id=plan_id,
                gate_decision_id=gate_decision_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_progressive_delivery_starts_total"
    )
    return state.__dict__

@app.post("/admin/progressive-delivery/{plan_id}/evaluate")
def evaluate_progressive_delivery(
    plan_id: str,
    evaluation_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        state, evaluation = (
            app.state.progressive_delivery_service
            .evaluate(
                plan_id=plan_id,
                evaluation_id=evaluation_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_progressive_delivery_evaluations_total"
    )
    if evaluation.action == "ROLLBACK":
        metrics.increment(
            "aslan_progressive_delivery_rollbacks_total"
        )
    if evaluation.action == "PROMOTE":
        metrics.increment(
            "aslan_progressive_delivery_promotions_total"
        )

    return {
        "state": state.__dict__,
        "evaluation": evaluation.__dict__,
    }

@app.post("/admin/progressive-delivery/{plan_id}/resume")
def resume_progressive_delivery(
    plan_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        state = (
            app.state.progressive_delivery_service
            .resume(plan_id=plan_id)
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    return state.__dict__

@app.get("/admin/progressive-delivery/{plan_id}/state")
def get_progressive_delivery_state(
    plan_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    state = (
        app.state.progressive_delivery_service
        .repository.get_state(plan_id)
    )
    if state is None:
        raise HTTPException(
            status_code=404,
            detail="Progressive delivery state bulunamadı",
        )
    return state.__dict__

@app.get("/admin/progressive-delivery/{plan_id}/evaluations")
def list_progressive_delivery_evaluations(
    plan_id: str,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.progressive_delivery_service
                .repository.list_evaluations(
                    plan_id,
                    limit=limit,
                )
            )
        ]
    }


@app.post("/admin/deployment-verification/sessions")
def create_deployment_verification_session(
    session_id: str,
    plan_id: str,
    deployment_slot: str,
    required_checks: int = Query(default=1, ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops", "mlops")
    ),
):
    try:
        session = (
            app.state.deployment_verification_service
            .create_session(
                session_id=session_id,
                plan_id=plan_id,
                deployment_slot=deployment_slot,
                required_checks=required_checks,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_deployment_verification_sessions_total"
    )
    return session.__dict__

@app.post("/admin/deployment-verification/{session_id}/checks")
def record_deployment_verification_check(
    session_id: str,
    check_id: str,
    check_type: str,
    name: str,
    passed: bool,
    detail: str,
    value: float | None = None,
    threshold: float | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops", "mlops")
    ),
):
    try:
        session, check = (
            app.state.deployment_verification_service
            .record_check(
                session_id=session_id,
                check_id=check_id,
                check_type=check_type,
                name=name,
                passed=passed,
                detail=detail,
                value=value,
                threshold=threshold,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_deployment_verification_checks_total"
    )
    if not check.passed:
        metrics.increment(
            "aslan_deployment_verification_failures_total"
        )
    return {
        "session": session.__dict__,
        "check": check.__dict__,
    }

@app.post("/admin/deployment-verification/{session_id}/finalize")
def finalize_deployment_verification(
    session_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops", "mlops")
    ),
):
    try:
        session = (
            app.state.deployment_verification_service
            .finalize(session_id=session_id)
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_deployment_verifications_completed_total"
    )
    return session.__dict__

@app.post("/admin/deployment-verification/{session_id}/rollback")
def execute_deployment_verification_rollback(
    session_id: str,
    reason: str | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops", "mlops")
    ),
):
    try:
        session = (
            app.state.deployment_verification_service
            .execute_rollback(
                session_id=session_id,
                reason=reason,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_deployment_rollbacks_executed_total"
    )
    return session.__dict__

@app.get("/admin/deployment-verification/{session_id}")
def get_deployment_verification_session(
    session_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops", "mlops")
    ),
):
    session = (
        app.state.deployment_verification_service
        .repository.get_session(session_id)
    )
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Verification session bulunamadı",
        )
    return {
        "session": session.__dict__,
        "checks": [
            item.__dict__
            for item in (
                app.state.deployment_verification_service
                .repository.list_checks(session_id)
            )
        ],
    }

@app.get("/admin/deployment-verification/plans/{plan_id}")
def list_deployment_verification_sessions(
    plan_id: str,
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops", "mlops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.deployment_verification_service
                .repository.list_sessions(
                    plan_id,
                    limit=limit,
                )
            )
        ]
    }


@app.post("/admin/deployment-safety/freezes")
def create_deployment_freeze(
    freeze_id: str,
    tenant_id: str,
    starts_at: int = Query(ge=1),
    ends_at: int = Query(ge=1),
    reason: str = Query(min_length=5),
    emergency_bypass_allowed: bool = Query(
        default=False
    ),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        freeze = (
            app.state.deployment_safety_service
            .create_freeze(
                freeze_id=freeze_id,
                tenant_id=tenant_id,
                starts_at=starts_at,
                ends_at=ends_at,
                reason=reason,
                emergency_bypass_allowed=(
                    emergency_bypass_allowed
                ),
                created_by=principal.subject,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_deployment_freezes_total"
    )
    return freeze.__dict__

@app.post("/admin/deployment-safety/approvals")
def create_deployment_approval(
    approval_id: str,
    tenant_id: str,
    release_id: str,
    role: str,
    decision: str,
    comment: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "ops",
            "mlops",
            "security",
        )
    ),
):
    try:
        approval = (
            app.state.deployment_safety_service
            .approve(
                approval_id=approval_id,
                tenant_id=tenant_id,
                release_id=release_id,
                role=role,
                actor=principal.subject,
                decision=decision,
                comment=comment,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return approval.__dict__

@app.post("/admin/deployment-safety/risk")
def calculate_deployment_risk(
    tenant_id: str,
    release_id: str,
    plan_id: str,
    verification_session_id: str,
    changed_files: int = Query(ge=0),
    affected_services: int = Query(ge=0),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        snapshot = (
            app.state.deployment_safety_service
            .calculate_risk(
                tenant_id=tenant_id,
                release_id=release_id,
                plan_id=plan_id,
                verification_session_id=(
                    verification_session_id
                ),
                changed_files=changed_files,
                affected_services=(
                    affected_services
                ),
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_deployment_risk_calculations_total"
    )
    return {
        **snapshot.__dict__,
        "reasons": list(snapshot.reasons),
    }

@app.post("/admin/deployment-safety/{tenant_id}/evaluate")
def evaluate_deployment_safety(
    tenant_id: str,
    decision_id: str,
    release_id: str,
    emergency: bool = Query(default=False),
    override: bool = Query(default=False),
    override_reason: str | None = None,
    required_roles: str = Query(
        default="ops,mlops"
    ),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    try:
        roles = tuple(
            item.strip()
            for item in required_roles.split(",")
            if item.strip()
        )
        decision = (
            app.state.deployment_safety_service
            .evaluate(
                decision_id=decision_id,
                tenant_id=tenant_id,
                release_id=release_id,
                emergency=emergency,
                override_actor=(
                    principal.subject
                    if override
                    else None
                ),
                override_reason=(
                    override_reason
                    if override
                    else None
                ),
                required_roles=roles,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_deployment_safety_evaluations_total"
    )
    if not decision.allowed:
        metrics.increment(
            "aslan_deployment_safety_blocks_total"
        )
    if decision.status == "OVERRIDDEN":
        metrics.increment(
            "aslan_deployment_safety_overrides_total"
        )
    return {
        **decision.__dict__,
        "approvals_required": list(
            decision.approvals_required
        ),
        "approvals_received": list(
            decision.approvals_received
        ),
    }

@app.get("/admin/deployment-safety/{tenant_id}/{release_id}/timeline")
def get_deployment_safety_timeline(
    tenant_id: str,
    release_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return {
        "items": list(
            app.state.deployment_safety_service
            .timeline(
                tenant_id=tenant_id,
                release_id=release_id,
            )
        )
    }

@app.get("/admin/deployment-safety/{tenant_id}/freezes")
def list_deployment_freezes(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.deployment_safety_service
                .repository.list_freezes(tenant_id)
            )
        ]
    }


@app.post("/admin/changes")
def create_change_request(
    change_id: str, tenant_id: str, release_id: str, title: str, description: str,
    change_type: str, risk_level: str, rollback_plan: str, test_evidence: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops")),
):
    try:
        change=app.state.change_management_service.create_change(
            change_id=change_id, tenant_id=tenant_id, release_id=release_id, title=title,
            description=description, change_type=change_type, risk_level=risk_level,
            owner=principal.subject, rollback_plan=rollback_plan,
            test_evidence=tuple(x.strip() for x in test_evidence.split(",") if x.strip()),
        )
    except ValueError as exc: raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {**change.__dict__, "test_evidence": list(change.test_evidence)}

@app.post("/admin/changes/{change_id}/submit")
def submit_change_request(change_id: str, principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops"))):
    try: change=app.state.change_management_service.submit(change_id=change_id)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {**change.__dict__, "test_evidence": list(change.test_evidence)}

@app.post("/admin/changes/{change_id}/approvals")
def approve_change_request(change_id: str, approval_id: str, role: str, decision: str, comment: str, principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security"))):
    try: change,approval=app.state.change_management_service.approve(approval_id=approval_id,change_id=change_id,role=role,actor=principal.subject,decision=decision,comment=comment)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError,RuntimeError) as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {"change":{**change.__dict__,"test_evidence":list(change.test_evidence)},"approval":approval.__dict__}

@app.post("/admin/changes/{change_id}/evidence")
def generate_release_evidence(change_id: str, evidence_id: str, manifest_sha256: str, sbom_sha256: str, test_summary: str, verification_session_id: str, safety_decision_id: str, principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops"))):
    try: e=app.state.change_management_service.generate_evidence(evidence_id=evidence_id,change_id=change_id,manifest_sha256=manifest_sha256,sbom_sha256=sbom_sha256,test_summary=test_summary,verification_session_id=verification_session_id,safety_decision_id=safety_decision_id)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    except (ValueError,RuntimeError) as exc: raise HTTPException(status_code=409, detail=str(exc)) from exc
    return e.__dict__

@app.get("/admin/changes/{change_id}/compliance")
def get_change_compliance(change_id: str, principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security"))):
    try: s=app.state.change_management_service.compliance(change_id=change_id)
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {**s.__dict__,"gaps":list(s.gaps)}

@app.get("/admin/changes/{change_id}/timeline")
def get_change_timeline(change_id: str, principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security"))):
    try: return {"items":list(app.state.change_management_service.timeline(change_id=change_id))}
    except KeyError as exc: raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.get("/admin/changes/tenant/{tenant_id}")
def list_change_requests(tenant_id: str, limit: int = Query(default=100, ge=1, le=500), principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security"))):
    return {"items":[{**x.__dict__,"test_evidence":list(x.test_evidence)} for x in app.state.change_management_service.repository.list_changes(tenant_id,limit=limit)]}

@app.post("/admin/compliance-attestations")
def create_compliance_attestation(
    attestation_id: str,
    change_id: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security")),
):
    try:
        item = app.state.compliance_attestation_service.attest(
            attestation_id=attestation_id,
            change_id=change_id,
            issued_by=principal.subject,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    metrics.increment("aslan_compliance_attestations_total")
    return item.__dict__

@app.get("/admin/compliance-attestations/{attestation_id}/verify")
def verify_compliance_attestation(
    attestation_id: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security")),
):
    try:
        result = app.state.compliance_attestation_service.verify(attestation_id=attestation_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    if not result["valid"]:
        metrics.increment("aslan_compliance_attestation_verification_failures_total")
    return result

@app.post("/admin/compliance-attestations/{change_id}/events")
def append_compliance_audit_event(
    change_id: str,
    event_type: str,
    payload: str,
    entry_id: str | None = None,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security")),
):
    try:
        parsed = __import__("json").loads(payload)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail="Payload geçerli JSON olmalıdır") from exc
    item = app.state.compliance_attestation_service.append_event(
        change_id=change_id,
        event_type=event_type,
        payload=parsed,
        entry_id=entry_id,
    )
    return item.__dict__

@app.get("/admin/compliance-attestations/{change_id}/chain/verify")
def verify_compliance_audit_chain(
    change_id: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security")),
):
    return app.state.compliance_attestation_service.verify_chain(change_id=change_id)

@app.get("/admin/compliance-attestations/{change_id}/bundle")
def export_compliance_bundle(
    change_id: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "security")),
):
    try:
        return app.state.compliance_attestation_service.export_bundle(change_id=change_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.post("/admin/transparency-log/entries")
def append_transparency_entry(
    entry_id: str,
    tenant_id: str,
    change_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "ops",
            "security",
        )
    ),
):
    try:
        entry = (
            app.state.transparency_log_service
            .append(
                entry_id=entry_id,
                tenant_id=tenant_id,
                change_id=change_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_transparency_entries_total"
    )
    return entry.__dict__

@app.post("/admin/transparency-log/checkpoints")
def create_transparency_checkpoint(
    checkpoint_id: str,
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "ops",
            "security",
        )
    ),
):
    try:
        checkpoint = (
            app.state.transparency_log_service
            .create_checkpoint(
                checkpoint_id=checkpoint_id,
                tenant_id=tenant_id,
            )
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_transparency_checkpoints_total"
    )
    return checkpoint.__dict__

@app.get("/public/transparency-log/{tenant_id}/entries/{entry_id}/proof")
def get_transparency_inclusion_proof(
    tenant_id: str,
    entry_id: str,
):
    try:
        proof = (
            app.state.transparency_log_service
            .inclusion_proof(
                tenant_id=tenant_id,
                entry_id=entry_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        **proof.__dict__,
        "audit_path": list(proof.audit_path),
    }

@app.post("/public/transparency-log/verify-proof")
def verify_transparency_inclusion_proof(
    entry_id: str,
    tenant_id: str,
    leaf_hash: str,
    leaf_index: int = Query(ge=0),
    tree_size: int = Query(ge=1),
    root_hash: str = Query(min_length=64, max_length=64),
    audit_path: str = Query(default=""),
):
    proof = InclusionProof(
        entry_id=entry_id,
        tenant_id=tenant_id,
        leaf_hash=leaf_hash,
        leaf_index=leaf_index,
        tree_size=tree_size,
        root_hash=root_hash,
        audit_path=tuple(
            item.strip()
            for item in audit_path.split(",")
            if item.strip()
        ),
        generated_at=0,
    )
    return {
        "valid": (
            app.state.transparency_log_service
            .verify_inclusion(proof=proof)
        )
    }

@app.get("/public/transparency-log/{tenant_id}/checkpoints/latest")
def get_latest_transparency_checkpoint(
    tenant_id: str,
):
    checkpoint = (
        app.state.transparency_log_service
        .repository.latest_checkpoint(tenant_id)
    )
    if checkpoint is None:
        raise HTTPException(
            status_code=404,
            detail="Transparency checkpoint bulunamadı",
        )
    return checkpoint.__dict__

@app.get("/public/transparency-log/{tenant_id}/verify-chain")
def verify_transparency_checkpoint_chain(
    tenant_id: str,
):
    result = (
        app.state.transparency_log_service
        .verify_checkpoint_chain(
            tenant_id=tenant_id
        )
    )
    if not result["valid"]:
        metrics.increment(
            "aslan_transparency_chain_failures_total"
        )
    return result


@app.post("/admin/transparency-witness/witnesses")
def register_transparency_witness(
    witness_id: str,
    tenant_id: str,
    key_id: str,
    shared_secret: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "security",
        )
    ),
):
    try:
        witness = (
            app.state.transparency_witness_service
            .register_witness(
                witness_id=witness_id,
                tenant_id=tenant_id,
                key_id=key_id,
                shared_secret=shared_secret,
            )
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_transparency_witnesses_total"
    )
    return {
        **witness.__dict__,
        "shared_secret": "***",
    }

@app.post("/admin/transparency-witness/checkpoints/{checkpoint_id}/sign")
def sign_transparency_checkpoint(
    checkpoint_id: str,
    signature_id: str,
    tenant_id: str,
    witness_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "security",
        )
    ),
):
    try:
        signature = (
            app.state.transparency_witness_service
            .sign_checkpoint(
                signature_id=signature_id,
                tenant_id=tenant_id,
                checkpoint_id=checkpoint_id,
                witness_id=witness_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_transparency_witness_signatures_total"
    )
    return signature.__dict__

@app.get("/public/transparency-witness/{tenant_id}/checkpoints/{checkpoint_id}/quorum")
def verify_transparency_checkpoint_quorum(
    tenant_id: str,
    checkpoint_id: str,
    required_witnesses: int = Query(
        default=2,
        ge=1,
    ),
):
    try:
        result = (
            app.state.transparency_witness_service
            .verify_quorum(
                tenant_id=tenant_id,
                checkpoint_id=checkpoint_id,
                required_witnesses=required_witnesses,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        **result.__dict__,
        "valid_witnesses": list(
            result.valid_witnesses
        ),
        "invalid_witnesses": list(
            result.invalid_witnesses
        ),
    }

@app.get("/public/transparency-witness/{tenant_id}/consistency")
def get_checkpoint_consistency_proof(
    tenant_id: str,
    from_checkpoint_id: str,
    to_checkpoint_id: str,
):
    try:
        proof = (
            app.state.transparency_witness_service
            .consistency_proof(
                tenant_id=tenant_id,
                from_checkpoint_id=(
                    from_checkpoint_id
                ),
                to_checkpoint_id=(
                    to_checkpoint_id
                ),
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

    return {
        **proof.__dict__,
        "appended_leaf_hashes": list(
            proof.appended_leaf_hashes
        ),
    }

@app.post("/public/transparency-witness/verify-consistency")
def verify_checkpoint_consistency_proof(
    tenant_id: str,
    from_checkpoint_id: str,
    to_checkpoint_id: str,
    from_tree_size: int = Query(ge=1),
    to_tree_size: int = Query(ge=1),
    from_root_hash: str = Query(
        min_length=64,
        max_length=64,
    ),
    to_root_hash: str = Query(
        min_length=64,
        max_length=64,
    ),
    appended_leaf_hashes: str = Query(default=""),
    proof_hash: str = Query(
        min_length=64,
        max_length=64,
    ),
):
    proof = CheckpointConsistencyProof(
        tenant_id=tenant_id,
        from_checkpoint_id=from_checkpoint_id,
        to_checkpoint_id=to_checkpoint_id,
        from_tree_size=from_tree_size,
        to_tree_size=to_tree_size,
        from_root_hash=from_root_hash,
        to_root_hash=to_root_hash,
        appended_leaf_hashes=tuple(
            item.strip()
            for item in appended_leaf_hashes.split(",")
            if item.strip()
        ),
        proof_hash=proof_hash,
        generated_at=0,
    )
    result = (
        app.state.transparency_witness_service
        .verify_consistency(proof=proof)
    )
    if not result["valid"]:
        metrics.increment(
            "aslan_transparency_consistency_failures_total"
        )
    return result

@app.post("/admin/governance/policies")
def create_governance_policy(
    policy_id: str, tenant_id: str, name: str, category: str,
    scope: str, rules: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "security", "ops")),
):
    try:
        item = app.state.governance_service.create_policy(
            policy_id=policy_id, tenant_id=tenant_id, name=name, category=category,
            scope=scope, owner=principal.subject,
            rules=tuple(x.strip() for x in rules.split(",") if x.strip()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {**item.__dict__, "rules": list(item.rules)}

@app.post("/admin/governance/policies/{policy_id}/transition")
def transition_governance_policy(
    policy_id: str, tenant_id: str, version: int = Query(ge=1), target_status: str = "REVIEW",
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "security", "ops")),
):
    try:
        item = app.state.governance_service.transition_policy(tenant_id=tenant_id, policy_id=policy_id, version=version, target_status=target_status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {**item.__dict__, "rules": list(item.rules)}

@app.post("/admin/governance/controls")
def create_governance_control(
    control_id: str, tenant_id: str, name: str, policy_ids: str, required_evidence_types: str = "",
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "security", "ops")),
):
    try:
        item = app.state.governance_service.create_control(
            control_id=control_id, tenant_id=tenant_id, name=name,
            policy_ids=tuple(x.strip() for x in policy_ids.split(",") if x.strip()),
            required_evidence_types=tuple(x.strip() for x in required_evidence_types.split(",") if x.strip()),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {**item.__dict__, "policy_ids": list(item.policy_ids), "required_evidence_types": list(item.required_evidence_types)}

@app.post("/admin/governance/evidence")
def collect_governance_evidence(
    evidence_id: str, tenant_id: str, evidence_type: str, source_system: str,
    source_reference: str, metadata_json: str = "{}",
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "security", "ops")),
):
    try:
        item = app.state.governance_service.collect_evidence(
            evidence_id=evidence_id, tenant_id=tenant_id, evidence_type=evidence_type,
            source_system=source_system, source_reference=source_reference,
            metadata=__import__("json").loads(metadata_json),
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.__dict__

@app.post("/admin/governance/evaluations")
def evaluate_governance_policy(
    evaluation_id: str, tenant_id: str, policy_id: str, resource: str,
    facts_json: str = "{}", evidence_ids: str = "",
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "security", "ops")),
):
    try:
        item = app.state.governance_service.evaluate_policy(
            evaluation_id=evaluation_id, tenant_id=tenant_id, policy_id=policy_id, resource=resource,
            facts=__import__("json").loads(facts_json),
            evidence_ids=tuple(x.strip() for x in evidence_ids.split(",") if x.strip()),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    return {**item.__dict__, "violations": list(item.violations), "evidence_ids": list(item.evidence_ids)}

@app.get("/admin/governance/{tenant_id}/report")
def get_governance_report(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "security", "ops")),
):
    return app.state.governance_service.compliance_report(tenant_id=tenant_id)


@app.post("/admin/governance/exceptions")
def create_governance_exception(
    exception_id: str,
    tenant_id: str,
    policy_id: str,
    resource: str,
    reason: str,
    risk_level: str,
    starts_at: int = Query(ge=1),
    expires_at: int = Query(ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        item = (
            app.state.governance_exception_service
            .create_exception(
                exception_id=exception_id,
                tenant_id=tenant_id,
                policy_id=policy_id,
                resource=resource,
                reason=reason,
                risk_level=risk_level,
                approved_by=principal.subject,
                starts_at=starts_at,
                expires_at=expires_at,
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.__dict__

@app.post("/admin/governance/exceptions/{exception_id}/risk")
def accept_governance_risk(
    exception_id: str,
    tenant_id: str,
    acceptance_id: str,
    residual_risk: str,
    compensating_controls: str,
    decision: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security")
    ),
):
    try:
        item = (
            app.state.governance_exception_service
            .accept_risk(
                acceptance_id=acceptance_id,
                tenant_id=tenant_id,
                exception_id=exception_id,
                risk_owner=principal.subject,
                residual_risk=residual_risk,
                compensating_controls=tuple(
                    token.strip()
                    for token in compensating_controls.split(",")
                    if token.strip()
                ),
                decision=decision,
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        **item.__dict__,
        "compensating_controls": list(
            item.compensating_controls
        ),
    }

@app.post("/admin/governance/framework-mappings")
def create_governance_framework_mapping(
    mapping_id: str,
    tenant_id: str,
    framework: str,
    framework_control: str,
    governance_control_id: str,
    evidence_types: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        item = (
            app.state.governance_exception_service
            .create_mapping(
                mapping_id=mapping_id,
                tenant_id=tenant_id,
                framework=framework,
                framework_control=framework_control,
                governance_control_id=governance_control_id,
                evidence_types=tuple(
                    token.strip()
                    for token in evidence_types.split(",")
                    if token.strip()
                ),
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return {
        **item.__dict__,
        "evidence_types": list(item.evidence_types),
    }

@app.get("/admin/governance/exceptions/{exception_id}")
def get_governance_exception_status(
    exception_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        return (
            app.state.governance_exception_service
            .exception_status(exception_id=exception_id)
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.get("/admin/governance/{tenant_id}/frameworks/{framework}")
def get_governance_framework_report(
    tenant_id: str,
    framework: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    return (
        app.state.governance_exception_service
        .framework_report(
            tenant_id=tenant_id,
            framework=framework,
        )
    )


@app.post("/admin/compliance/{tenant_id}/monitor")
def monitor_continuous_compliance(
    tenant_id: str,
    snapshot_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "security",
            "ops",
        )
    ),
):
    snapshot = (
        app.state.continuous_compliance_service
        .monitor(
            snapshot_id=snapshot_id,
            tenant_id=tenant_id,
        )
    )
    metrics.increment(
        "aslan_compliance_snapshots_total"
    )
    return {
        **snapshot.__dict__,
        "gaps": list(snapshot.gaps),
    }

@app.get("/admin/compliance/{tenant_id}/drifts")
def list_compliance_drifts(
    tenant_id: str,
    limit: int = Query(
        default=100,
        ge=1,
        le=500,
    ),
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "security",
            "ops",
        )
    ),
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.continuous_compliance_service
                .repository.list_drifts(
                    tenant_id,
                    limit=limit,
                )
            )
        ]
    }

@app.post("/admin/compliance/remediations")
def create_compliance_remediation(
    action_id: str,
    tenant_id: str,
    drift_id: str,
    action_type: str,
    assignee: str,
    due_at: int = Query(ge=1),
    detail: str = Query(min_length=5),
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "security",
            "ops",
        )
    ),
):
    try:
        action = (
            app.state.continuous_compliance_service
            .create_remediation(
                action_id=action_id,
                tenant_id=tenant_id,
                drift_id=drift_id,
                action_type=action_type,
                assignee=assignee,
                due_at=due_at,
                detail=detail,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    metrics.increment(
        "aslan_compliance_remediations_total"
    )
    return action.__dict__

@app.post("/admin/compliance/remediations/{action_id}/transition")
def transition_compliance_remediation(
    action_id: str,
    target_status: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "security",
            "ops",
        )
    ),
):
    try:
        return (
            app.state.continuous_compliance_service
            .transition_remediation(
                action_id=action_id,
                target_status=target_status,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except RuntimeError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc

@app.get("/admin/compliance/{tenant_id}/timeline")
def get_compliance_timeline(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "security",
            "ops",
        )
    ),
):
    return {
        "items": list(
            app.state.continuous_compliance_service
            .timeline(tenant_id=tenant_id)
        )
    }

@app.get("/admin/compliance/{tenant_id}/snapshots")
def list_compliance_snapshots(
    tenant_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "security",
            "ops",
        )
    ),
):
    return {
        "items": [
            {
                **item.__dict__,
                "gaps": list(item.gaps),
            }
            for item in (
                app.state.continuous_compliance_service
                .repository.list_snapshots(
                    tenant_id
                )
            )
        ]
    }


@app.post("/admin/audits")
def create_audit_plan(
    audit_id: str,
    tenant_id: str,
    framework: str,
    scope: str,
    starts_at: int = Query(ge=1),
    ends_at: int = Query(ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        item = (
            app.state.audit_orchestration_service
            .create_audit(
                audit_id=audit_id,
                tenant_id=tenant_id,
                framework=framework,
                scope=scope,
                lead_auditor=principal.subject,
                starts_at=starts_at,
                ends_at=ends_at,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.__dict__

@app.post("/admin/audits/{audit_id}/transition")
def transition_audit_plan(
    audit_id: str,
    target_status: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        return (
            app.state.audit_orchestration_service
            .transition_audit(
                audit_id=audit_id,
                target_status=target_status,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@app.post("/admin/audits/{audit_id}/evidence-requests")
def create_audit_evidence_request(
    audit_id: str,
    request_id: str,
    control_id: str,
    evidence_type: str,
    assignee: str,
    due_at: int = Query(ge=1),
    note: str = Query(default=""),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        item = (
            app.state.audit_orchestration_service
            .create_evidence_request(
                request_id=request_id,
                audit_id=audit_id,
                control_id=control_id,
                evidence_type=evidence_type,
                assignee=assignee,
                due_at=due_at,
                note=note,
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.__dict__

@app.post("/admin/audits/evidence-requests/{request_id}/fulfill")
def fulfill_audit_evidence_request(
    request_id: str,
    evidence_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        return (
            app.state.audit_orchestration_service
            .fulfill_evidence_request(
                request_id=request_id,
                evidence_id=evidence_id,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@app.post("/admin/audits/{audit_id}/findings")
def create_audit_finding(
    audit_id: str,
    finding_id: str,
    control_id: str,
    severity: str,
    title: str,
    detail: str,
    owner: str,
    due_at: int = Query(ge=1),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        item = (
            app.state.audit_orchestration_service
            .create_finding(
                finding_id=finding_id,
                audit_id=audit_id,
                control_id=control_id,
                severity=severity,
                title=title,
                detail=detail,
                owner=owner,
                due_at=due_at,
            )
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    return item.__dict__

@app.post("/admin/audits/findings/{finding_id}/transition")
def transition_audit_finding(
    finding_id: str,
    target_status: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        return (
            app.state.audit_orchestration_service
            .transition_finding(
                finding_id=finding_id,
                target_status=target_status,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

@app.get("/admin/audits/{audit_id}/readiness")
def get_audit_readiness(
    audit_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        report = (
            app.state.audit_orchestration_service
            .readiness_report(audit_id=audit_id)
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        **report.__dict__,
        "gaps": list(report.gaps),
    }

@app.get("/admin/audits/{audit_id}/timeline")
def get_audit_timeline(
    audit_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "security", "ops")
    ),
):
    try:
        return {
            "items": list(
                app.state.audit_orchestration_service
                .timeline(audit_id=audit_id)
            )
        }
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/")
def mvp_web_app():
    return FileResponse(
        __import__("pathlib").Path(__file__).parent
        / "static"
        / "index.html"
    )

@app.post("/mvp/clubs")
def mvp_create_club(
    club_id: str,
    name: str,
    country: str,
):
    try:
        return (
            app.state.mvp_workspace_service
            .create_club(
                club_id=club_id,
                name=name,
                country=country,
            )
            .__dict__
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.get("/mvp/clubs")
def mvp_list_clubs():
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.mvp_workspace_service
                .repository.list_clubs()
            )
        ]
    }

@app.post("/mvp/players")
def mvp_create_player(
    player_id: str,
    club_id: str,
    name: str,
    position: str,
    age: int = Query(ge=14, le=50),
    market_value: float = Query(ge=0),
):
    try:
        return (
            app.state.mvp_workspace_service
            .create_player(
                player_id=player_id,
                club_id=club_id,
                name=name,
                position=position,
                age=age,
                market_value=market_value,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

@app.post("/mvp/matches")
def mvp_create_match(
    match_id: str,
    club_id: str,
    opponent: str,
    competition: str,
    kickoff_at: int = Query(ge=1),
    venue: str = Query(pattern="^(HOME|AWAY)$"),
):
    try:
        return (
            app.state.mvp_workspace_service
            .create_match(
                match_id=match_id,
                club_id=club_id,
                opponent=opponent,
                competition=competition,
                kickoff_at=kickoff_at,
                venue=venue,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/mvp/matches/{match_id}/complete")
def mvp_complete_match(
    match_id: str,
    club_id: str,
    goals_for: int = Query(ge=0),
    goals_against: int = Query(ge=0),
):
    try:
        return (
            app.state.mvp_workspace_service
            .complete_match(
                match_id=match_id,
                club_id=club_id,
                goals_for=goals_for,
                goals_against=goals_against,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.get("/mvp/clubs/{club_id}/dashboard")
def mvp_dashboard(club_id: str):
    try:
        return (
            app.state.mvp_workspace_service
            .dashboard(club_id=club_id)
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.put("/mvp/players/{player_id}")
def mvp_update_player(
    player_id: str,
    club_id: str,
    name: str,
    position: str,
    age: int = Query(ge=14, le=50),
    market_value: float = Query(ge=0),
):
    try:
        return (
            app.state.mvp_workspace_service
            .update_player(
                player_id=player_id,
                club_id=club_id,
                name=name,
                position=position,
                age=age,
                market_value=market_value,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.delete("/mvp/players/{player_id}")
def mvp_delete_player(
    player_id: str,
    club_id: str,
):
    try:
        app.state.mvp_workspace_service.delete_player(
            player_id=player_id,
            club_id=club_id,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {"deleted": True}

@app.post("/mvp/demo")
def mvp_seed_demo():
    return (
        app.state.mvp_workspace_service
        .seed_demo()
    )

@app.get("/mvp/clubs/{club_id}/players.csv")
def mvp_export_players_csv(
    club_id: str,
):
    club = (
        app.state.mvp_workspace_service
        .repository.get_club(club_id)
    )
    if club is None:
        raise HTTPException(
            status_code=404,
            detail="Kulüp bulunamadı",
        )

    output = __import__("io").StringIO()
    writer = __import__("csv").writer(output)
    writer.writerow([
        "player_id",
        "name",
        "position",
        "age",
        "market_value",
    ])
    for item in (
        app.state.mvp_workspace_service
        .repository.list_players(club_id)
    ):
        writer.writerow([
            item.player_id,
            item.name,
            item.position,
            item.age,
            item.market_value,
        ])

    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv; charset=utf-8",
    )
    response.headers["Content-Disposition"] = (
        f'attachment; filename="{club_id}-players.csv"'
    )
    return response


@app.post("/mvp/players/{player_id}/availability")
def mvp_set_player_availability(
    player_id: str,
    club_id: str,
    availability: str,
    note: str = Query(default=""),
):
    try:
        return (
            app.state.mvp_workspace_service
            .set_player_availability(
                club_id=club_id,
                player_id=player_id,
                availability=availability,
                note=note,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/trainings")
def mvp_create_training(
    session_id: str,
    club_id: str,
    title: str,
    starts_at: int = Query(ge=1),
    focus: str = Query(default=""),
):
    try:
        return (
            app.state.mvp_workspace_service
            .create_training(
                session_id=session_id,
                club_id=club_id,
                title=title,
                starts_at=starts_at,
                focus=focus,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/trainings/{session_id}/attendance")
def mvp_record_training_attendance(
    session_id: str,
    player_id: str,
    status: str,
    note: str = Query(default=""),
):
    try:
        return (
            app.state.mvp_workspace_service
            .record_attendance(
                session_id=session_id,
                player_id=player_id,
                status=status,
                note=note,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/matches/{match_id}/squad")
def mvp_set_match_squad(
    match_id: str,
    club_id: str,
    player_ids: str,
):
    try:
        squad = (
            app.state.mvp_workspace_service
            .set_match_squad(
                match_id=match_id,
                club_id=club_id,
                player_ids=tuple(
                    item.strip()
                    for item in player_ids.split(",")
                    if item.strip()
                ),
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **squad.__dict__,
        "player_ids": list(squad.player_ids),
    }


@app.post("/mvp/matches/{match_id}/performances")
def mvp_record_player_performance(
    match_id: str,
    club_id: str,
    player_id: str,
    minutes: int = Query(ge=0, le=130),
    goals: int = Query(ge=0),
    assists: int = Query(ge=0),
    rating: float = Query(ge=0, le=10),
    note: str = Query(default=""),
):
    try:
        return (
            app.state.mvp_workspace_service
            .record_player_performance(
                match_id=match_id,
                club_id=club_id,
                player_id=player_id,
                minutes=minutes,
                goals=goals,
                assists=assists,
                rating=rating,
                note=note,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/matches/{match_id}/report")
def mvp_save_match_report(
    match_id: str,
    club_id: str,
    summary: str,
    positives: str = Query(default=""),
    improvements: str = Query(default=""),
):
    try:
        return (
            app.state.mvp_workspace_service
            .save_match_report(
                match_id=match_id,
                club_id=club_id,
                summary=summary,
                positives=positives,
                improvements=improvements,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/clubs/{club_id}/form")
def mvp_player_form(club_id: str):
    club = (
        app.state.mvp_workspace_service
        .repository.get_club(club_id)
    )
    if club is None:
        raise HTTPException(
            status_code=404,
            detail="Kulüp bulunamadı",
        )
    return {
        "items": list(
            app.state.mvp_workspace_service
            .player_form(club_id=club_id)
        )
    }


@app.post("/mvp/opponents")
def mvp_save_opponent_profile(
    opponent_id: str,
    club_id: str,
    name: str,
    formation: str = Query(default=""),
    strengths: str = Query(default=""),
    weaknesses: str = Query(default=""),
    key_players: str = Query(default=""),
    notes: str = Query(default=""),
):
    try:
        item = (
            app.state.mvp_workspace_service
            .save_opponent_profile(
                opponent_id=opponent_id,
                club_id=club_id,
                name=name,
                formation=formation,
                strengths=tuple(
                    token.strip()
                    for token in strengths.split(",")
                    if token.strip()
                ),
                weaknesses=tuple(
                    token.strip()
                    for token in weaknesses.split(",")
                    if token.strip()
                ),
                key_players=tuple(
                    token.strip()
                    for token in key_players.split(",")
                    if token.strip()
                ),
                notes=notes,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "strengths": list(item.strengths),
        "weaknesses": list(item.weaknesses),
        "key_players": list(item.key_players),
    }

@app.post("/mvp/matches/{match_id}/preparations")
def mvp_create_match_preparation(
    match_id: str,
    preparation_id: str,
    club_id: str,
    opponent_id: str,
    tactical_plan: str,
    pressing_plan: str = Query(default=""),
    set_piece_plan: str = Query(default=""),
    objectives: str = Query(default=""),
):
    try:
        item = (
            app.state.mvp_workspace_service
            .create_match_preparation(
                preparation_id=preparation_id,
                match_id=match_id,
                club_id=club_id,
                opponent_id=opponent_id,
                tactical_plan=tactical_plan,
                pressing_plan=pressing_plan,
                set_piece_plan=set_piece_plan,
                objectives=tuple(
                    token.strip()
                    for token in objectives.split(",")
                    if token.strip()
                ),
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "objectives": list(item.objectives),
    }

@app.post("/mvp/preparations/{preparation_id}/transition")
def mvp_transition_match_preparation(
    preparation_id: str,
    target_status: str,
):
    try:
        item = (
            app.state.mvp_workspace_service
            .transition_preparation(
                preparation_id=preparation_id,
                target_status=target_status,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "objectives": list(item.objectives),
    }

@app.post("/mvp/auth/login")
def mvp_auth_login(username: str, password: str):
    try:return app.state.mvp_auth_service.login(username=username,password=password).__dict__
    except MVPAuthError as exc:raise HTTPException(status_code=401,detail=str(exc)) from exc

@app.get("/mvp/auth/me")
def mvp_auth_me(token: str):
    try:return app.state.mvp_auth_service.require_session(token).__dict__
    except MVPAuthError as exc:raise HTTPException(status_code=401,detail=str(exc)) from exc

@app.post("/mvp/auth/logout")
def mvp_auth_logout(token: str):
    app.state.mvp_auth_service.logout(token);return {"logged_out":True}


@app.get("/mvp/mobile/config")
def mvp_mobile_config():
    return {
        "api_version": "build-003",
        "features": [
            "AUTH",
            "DASHBOARD",
            "PLAYERS",
            "MATCHES",
            "INTEGRATIONS",
            "MATCH_INTELLIGENCE",
            "ELO",
            "XG",
            "SCENARIOS",
            "CALIBRATION",
            "ENSEMBLE",
            "DATA_QUALITY",
            "UNCERTAINTY_INTERVALS",
            "LINEUP_IMPACT",
            "TACTICAL_MATCHUP",
            "MONTE_CARLO",
            "FIRST_HALF_PROBABILITIES",
            "MATCH_CONTEXT",
            "LIVE_PREDICTION",
            "EXPLAINABILITY",
            "MODEL_REGISTRY",
            "ROLLING_BACKTEST",
            "DRIFT_DETECTION",
            "COMPETITION_NORMALIZATION",
            "BATCH_PREDICTION",
            "PREDICTION_ALERTS",
            "DECISION_REPORT",
            "HUMAN_REVIEW",
            "MODEL_BENCHMARK",
            "RELIABILITY_DIAGRAM",
            "PREDICTION_AUDIT",
            "SHAREABLE_REPORT",
            "POST_MATCH_LEARNING",
            "OPPONENT_MEMORY",
            "SIMILAR_MATCHES",
            "RECALIBRATION_ADVISOR",
            "WALK_FORWARD_BACKTEST",
            "LEAKAGE_GUARD",
            "REPRODUCIBILITY",
            "SEASON_PERFORMANCE",
            "RELEASE_GATE",
            "END_TO_END_PIPELINE",
            "PILOT_READINESS",
            "SECURITY_AUDIT",
            "BACKUP_VALIDATION",
            "API_CONTRACT_SNAPSHOT",
            "SMOKE_TEST",
            "PILOT_TELEMETRY",
            "INCIDENT_MANAGEMENT",
            "HEALTH_SCORE",
            "OPERATION_ALARMS",
            "PRODUCT_ANALYTICS",
            "PILOT_FEEDBACK",
            "FEATURE_ADOPTION",
            "IMPROVEMENT_PRIORITIES",
            "FEATURE_FLAGS",
            "AB_EXPERIMENTS",
            "CONTROLLED_ROLLOUT",
            "SAFE_ROLLBACK",
            "FINAL_PILOT_PACKAGE",
            "ONE_COMMAND_SETUP",
            "PILOT_ACCEPTANCE",
            "IDEMPOTENCY_CHECK",
            "FINAL_FINGERPRINT",
            "IMPORT_QUARANTINE",
            "DELIVERY_MANIFEST",
            "ROLLBACK_PLAN",
            "PRODUCTION_PREFLIGHT",
            "MIGRATION_PREFLIGHT",
            "DISASTER_RECOVERY_DRILL",
            "SIGNED_RELEASE_MANIFEST",
            "SBOM",
            "LICENSE_AUDIT",
            "PACKAGE_INTEGRITY",
            "REPRODUCIBLE_BUILD",
        ],
        "demo_users": [
            {
                "username": "coach",
                "role": "COACH",
            },
            {
                "username": "analyst",
                "role": "ANALYST",
            },
        ],
    }


@app.post("/mvp/integrations/connections")
def mvp_create_provider_connection(
    connection_id: str,
    club_id: str,
    provider: str,
    base_url: str = Query(default=""),
    external_club_id: str = Query(default=""),
):
    try:
        return (
            app.state.mvp_integration_service
            .create_connection(
                connection_id=connection_id,
                club_id=club_id,
                provider=provider,
                base_url=base_url,
                external_club_id=external_club_id,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except IntegrationValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/integrations/{club_id}/connections")
def mvp_list_provider_connections(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.mvp_integration_service
                .repository.list_connections(
                    club_id
                )
            )
        ]
    }

@app.post("/mvp/integrations/{club_id}/players/csv")
def mvp_import_players_csv(
    club_id: str,
    sync_id: str,
    csv_text: str,
):
    try:
        item = (
            app.state.mvp_integration_service
            .import_players_csv(
                sync_id=sync_id,
                club_id=club_id,
                csv_text=csv_text,
            )
        )
    except IntegrationValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "errors": list(item.errors),
    }

@app.post("/mvp/integrations/{club_id}/fixtures/csv")
def mvp_import_fixtures_csv(
    club_id: str,
    sync_id: str,
    csv_text: str,
):
    try:
        item = (
            app.state.mvp_integration_service
            .import_fixtures_csv(
                sync_id=sync_id,
                club_id=club_id,
                csv_text=csv_text,
            )
        )
    except IntegrationValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "errors": list(item.errors),
    }

@app.get("/mvp/integrations/{club_id}/syncs")
def mvp_list_sync_runs(
    club_id: str,
):
    return {
        "items": [
            {
                **item.__dict__,
                "errors": list(item.errors),
            }
            for item in (
                app.state.mvp_integration_service
                .repository.list_syncs(
                    club_id
                )
            )
        ]
    }

@app.post("/mvp/integrations/{connection_id}/preview")
def mvp_provider_payload_preview(
    connection_id: str,
    payload_json: str,
):
    try:
        return (
            app.state.mvp_integration_service
            .provider_payload_preview(
                connection_id=connection_id,
                payload_json=payload_json,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except IntegrationValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.post("/mvp/intelligence/{club_id}/derive-profile")
def derive_match_intelligence_profile(
    club_id: str,
    profile_id: str,
):
    try:
        return (
            app.state.match_intelligence_service
            .derive_club_profile(
                profile_id=profile_id,
                club_id=club_id,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.post("/mvp/intelligence/{club_id}/opponent-profiles")
def save_match_intelligence_opponent_profile(
    club_id: str,
    profile_id: str,
    team_name: str,
    attack_rating: float = Query(ge=0, le=2),
    defence_rating: float = Query(ge=0, le=2),
    form_rating: float = Query(ge=0, le=2),
    home_rating: float = Query(ge=0, le=2),
    away_rating: float = Query(ge=0, le=2),
    goals_for_average: float = Query(ge=0),
    goals_against_average: float = Query(ge=0),
    sample_size: int = Query(ge=0),
    elo_rating: float = Query(default=1500, ge=1000, le=2500),
    xg_for_average: float = Query(default=0, ge=0),
    xg_against_average: float = Query(default=0, ge=0),
):
    try:
        return (
            app.state.match_intelligence_service
            .save_opponent_profile(
                profile_id=profile_id,
                club_id=club_id,
                team_name=team_name,
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
            )
            .__dict__
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/intelligence/{club_id}/predict")
def predict_match_score(
    club_id: str,
    prediction_id: str,
    match_id: str,
    club_profile_id: str,
    opponent_profile_id: str,
    unavailable_impact: float = Query(default=0, ge=0, le=0.70),
    opponent_unavailable_impact: float = Query(
        default=0,
        ge=0,
        le=0.70,
    ),
):
    try:
        item = (
            app.state.match_intelligence_service
            .predict(
                prediction_id=prediction_id,
                club_id=club_id,
                match_id=match_id,
                club_profile_id=club_profile_id,
                opponent_profile_id=opponent_profile_id,
                unavailable_impact=unavailable_impact,
                opponent_unavailable_impact=opponent_unavailable_impact,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "likely_scores": list(item.likely_scores),
        "factors": list(item.factors),
        "risks": list(item.risks),
    }

@app.get("/mvp/intelligence/{club_id}/predictions")
def list_match_predictions(club_id: str):
    return {
        "items": [
            {
                **item.__dict__,
                "likely_scores": list(item.likely_scores),
                "factors": list(item.factors),
                "risks": list(item.risks),
            }
            for item in (
                app.state.match_intelligence_service
                .repository.list_predictions(club_id)
            )
        ]
    }

@app.post("/mvp/intelligence/predictions/{prediction_id}/evaluate")
def evaluate_match_prediction(
    prediction_id: str,
    evaluation_id: str,
    actual_home_goals: int = Query(ge=0),
    actual_away_goals: int = Query(ge=0),
):
    try:
        return (
            app.state.match_intelligence_service
            .evaluate(
                evaluation_id=evaluation_id,
                prediction_id=prediction_id,
                actual_home_goals=actual_home_goals,
                actual_away_goals=actual_away_goals,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.get("/mvp/intelligence/{club_id}/accuracy")
def match_prediction_accuracy(club_id: str):
    return (
        app.state.match_intelligence_service
        .accuracy_report(club_id=club_id)
    )


@app.post("/mvp/intelligence/predictions/{prediction_id}/scenarios")
def create_prediction_scenarios(
    prediction_id: str,
):
    try:
        items = (
            app.state.match_intelligence_service
            .create_scenarios(
                prediction_id=prediction_id
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        "items": [
            item.__dict__
            for item in items
        ]
    }

@app.get("/mvp/intelligence/predictions/{prediction_id}/scenarios")
def list_prediction_scenarios(
    prediction_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.match_intelligence_service
                .repository.list_scenarios(
                    prediction_id
                )
            )
        ]
    }

@app.post("/mvp/intelligence/{club_id}/calibrate")
def calibrate_match_intelligence(
    club_id: str,
    calibration_id: str,
):
    try:
        return (
            app.state.match_intelligence_service
            .calibrate(
                calibration_id=calibration_id,
                club_id=club_id,
            )
            .__dict__
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/intelligence/{club_id}/backtest")
def match_intelligence_backtest(
    club_id: str,
):
    return (
        app.state.match_intelligence_service
        .backtest_report(club_id=club_id)
    )


@app.get("/mvp/intelligence/{club_id}/availability-impact")
def automatic_availability_impact(
    club_id: str,
):
    return {
        "club_id": club_id,
        "unavailable_impact": (
            app.state.match_intelligence_service
            .automatic_unavailable_impact(
                club_id=club_id
            )
        ),
    }

@app.post("/mvp/intelligence/{club_id}/data-quality")
def create_match_data_quality_report(
    club_id: str,
    report_id: str,
    club_profile_id: str,
    opponent_profile_id: str,
):
    try:
        item = (
            app.state.match_intelligence_service
            .data_quality_report(
                report_id=report_id,
                club_id=club_id,
                club_profile_id=club_profile_id,
                opponent_profile_id=opponent_profile_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "warnings": list(item.warnings),
    }

@app.post("/mvp/intelligence/predictions/{prediction_id}/ensemble")
def create_match_prediction_ensemble(
    prediction_id: str,
    ensemble_id: str,
    data_quality_report_id: str,
):
    try:
        item = (
            app.state.match_intelligence_service
            .create_ensemble(
                ensemble_id=ensemble_id,
                prediction_id=prediction_id,
                data_quality_report_id=data_quality_report_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
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

@app.get("/mvp/intelligence/predictions/{prediction_id}/brief")
def match_analysis_brief(
    prediction_id: str,
    ensemble_id: str | None = None,
):
    try:
        return (
            app.state.match_intelligence_service
            .analysis_brief(
                prediction_id=prediction_id,
                ensemble_id=ensemble_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@app.post("/mvp/intelligence/{club_id}/lineup-impact")
def create_lineup_impact_report(
    club_id: str,
    report_id: str,
    match_id: str,
    selected_player_ids: str,
):
    try:
        item = (
            app.state.match_intelligence_service
            .lineup_impact_report(
                report_id=report_id,
                club_id=club_id,
                match_id=match_id,
                selected_player_ids=tuple(
                    token.strip()
                    for token in selected_player_ids.split(",")
                    if token.strip()
                ),
            )
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "selected_player_ids": list(
            item.selected_player_ids
        ),
        "warnings": list(item.warnings),
    }

@app.post("/mvp/intelligence/{club_id}/tactical-matchup")
def create_tactical_matchup(
    club_id: str,
    matchup_id: str,
    match_id: str,
    own_style: str,
    opponent_style: str,
):
    try:
        item = (
            app.state.match_intelligence_service
            .tactical_matchup(
                matchup_id=matchup_id,
                club_id=club_id,
                match_id=match_id,
                own_style=own_style,
                opponent_style=opponent_style,
            )
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "notes": list(item.notes),
    }

@app.post("/mvp/intelligence/predictions/{prediction_id}/simulate")
def run_monte_carlo_simulation(
    prediction_id: str,
    simulation_id: str,
    iterations: int = Query(default=10000, ge=1000, le=100000),
    lineup_report_id: str | None = None,
    tactical_matchup_id: str | None = None,
    context_id: str | None = None,
):
    try:
        item = (
            app.state.match_intelligence_service
            .monte_carlo_simulation(
                simulation_id=simulation_id,
                prediction_id=prediction_id,
                iterations=iterations,
                lineup_report_id=lineup_report_id,
                tactical_matchup_id=tactical_matchup_id,
                context_id=context_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "score_distribution": list(
            item.score_distribution
        ),
    }

@app.get("/mvp/intelligence/predictions/{prediction_id}/simulations")
def list_monte_carlo_simulations(
    prediction_id: str,
):
    return {
        "items": [
            {
                **item.__dict__,
                "score_distribution": list(
                    item.score_distribution
                ),
            }
            for item in (
                app.state.match_intelligence_service
                .repository.list_simulations(
                    prediction_id
                )
            )
        ]
    }


@app.post("/mvp/intelligence/{club_id}/match-context")
def create_match_context_report(
    club_id: str,
    context_id: str,
    match_id: str,
    league_strength: float = Query(ge=0.5, le=1.5),
    rest_days: int = Query(ge=0),
    opponent_rest_days: int = Query(ge=0),
    travel_km: float = Query(ge=0),
    temperature_c: float = Query(),
    wind_kmh: float = Query(ge=0),
    precipitation_mm: float = Query(ge=0),
    referee_card_rate: float = Query(ge=0),
):
    try:
        item = (
            app.state.match_intelligence_service
            .match_context_report(
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
            )
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "warnings": list(item.warnings),
    }

@app.post("/mvp/intelligence/predictions/{prediction_id}/live")
def update_live_match_prediction(
    prediction_id: str,
    state_id: str,
    minute: int = Query(ge=0, le=130),
    home_goals: int = Query(ge=0),
    away_goals: int = Query(ge=0),
    home_red_cards: int = Query(default=0, ge=0),
    away_red_cards: int = Query(default=0, ge=0),
    home_xg_live: float = Query(default=0, ge=0),
    away_xg_live: float = Query(default=0, ge=0),
):
    try:
        return (
            app.state.match_intelligence_service
            .live_update(
                state_id=state_id,
                prediction_id=prediction_id,
                minute=minute,
                home_goals=home_goals,
                away_goals=away_goals,
                home_red_cards=home_red_cards,
                away_red_cards=away_red_cards,
                home_xg_live=home_xg_live,
                away_xg_live=away_xg_live,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/intelligence/predictions/{prediction_id}/live")
def list_live_match_predictions(
    prediction_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.match_intelligence_service
                .repository.list_live_states(
                    prediction_id
                )
            )
        ]
    }

@app.post("/mvp/intelligence/predictions/{prediction_id}/explain")
def explain_match_prediction(
    prediction_id: str,
    report_id: str,
    lineup_report_id: str | None = None,
    tactical_matchup_id: str | None = None,
    context_id: str | None = None,
):
    try:
        item = (
            app.state.match_intelligence_service
            .explain_prediction(
                report_id=report_id,
                prediction_id=prediction_id,
                lineup_report_id=lineup_report_id,
                tactical_matchup_id=tactical_matchup_id,
                context_id=context_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "contributions": list(item.contributions),
    }


@app.post("/mvp/intelligence/{club_id}/models")
def register_match_intelligence_model(
    club_id: str,
    model_id: str,
    model_version: str,
    competition: str = Query(default="ALL"),
    feature_set: str = Query(default=""),
    training_sample_size: int = Query(ge=0),
    validation_brier_score: float = Query(ge=0),
    validation_log_loss: float = Query(ge=0),
    status: str = Query(default="CANDIDATE"),
):
    try:
        item = (
            app.state.match_intelligence_service
            .register_model(
                model_id=model_id,
                club_id=club_id,
                model_version=model_version,
                competition=competition,
                feature_set=tuple(
                    token.strip()
                    for token in feature_set.split(",")
                    if token.strip()
                ),
                training_sample_size=training_sample_size,
                validation_brier_score=validation_brier_score,
                validation_log_loss=validation_log_loss,
                status=status,
            )
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "feature_set": list(item.feature_set),
    }

@app.post("/mvp/intelligence/models/{model_id}/promote")
def promote_match_intelligence_model(
    model_id: str,
):
    try:
        item = (
            app.state.match_intelligence_service
            .promote_model(model_id=model_id)
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "feature_set": list(item.feature_set),
    }

@app.get("/mvp/intelligence/{club_id}/models")
def list_match_intelligence_models(
    club_id: str,
):
    return {
        "items": [
            {
                **item.__dict__,
                "feature_set": list(
                    item.feature_set
                ),
            }
            for item in (
                app.state.match_intelligence_service
                .repository.list_models(club_id)
            )
        ]
    }

@app.get("/mvp/intelligence/{club_id}/competition-strength")
def match_competition_strength(
    club_id: str,
    competition: str,
):
    return (
        app.state.match_intelligence_service
        .competition_strength(
            club_id=club_id,
            competition=competition,
        )
    )

@app.post("/mvp/intelligence/predictions/{prediction_id}/snapshot")
def snapshot_match_prediction(
    prediction_id: str,
    snapshot_id: str,
    model_id: str,
    data_quality_score: float = Query(ge=0, le=100),
):
    try:
        return (
            app.state.match_intelligence_service
            .snapshot_prediction(
                snapshot_id=snapshot_id,
                prediction_id=prediction_id,
                model_id=model_id,
                data_quality_score=data_quality_score,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.get("/mvp/intelligence/{club_id}/rolling-backtest")
def rolling_match_backtest(
    club_id: str,
    window_size: int = Query(default=20, ge=5, le=100),
):
    try:
        return (
            app.state.match_intelligence_service
            .rolling_backtest(
                club_id=club_id,
                window_size=window_size,
            )
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/intelligence/{club_id}/drift")
def create_model_drift_report(
    club_id: str,
    drift_id: str,
    model_id: str,
    window_size: int = Query(default=10, ge=5, le=100),
):
    try:
        item = (
            app.state.match_intelligence_service
            .drift_report(
                drift_id=drift_id,
                club_id=club_id,
                model_id=model_id,
                window_size=window_size,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "warnings": list(item.warnings),
    }


@app.post("/mvp/intelligence/{club_id}/batch-predict")
def batch_predict_upcoming_matches(
    club_id: str,
    club_profile_id: str,
    opponent_profile_id: str,
    limit: int = Query(default=10, ge=1, le=50),
):
    try:
        items = (
            app.state.match_intelligence_service
            .batch_predict_upcoming(
                club_id=club_id,
                club_profile_id=club_profile_id,
                opponent_profile_id=opponent_profile_id,
                limit=limit,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        "items": [
            {
                **item.__dict__,
                "likely_scores": list(item.likely_scores),
                "factors": list(item.factors),
                "risks": list(item.risks),
            }
            for item in items
        ]
    }

@app.post("/mvp/intelligence/predictions/{prediction_id}/alerts")
def generate_prediction_alerts(
    prediction_id: str,
    club_id: str,
    data_quality_score: float = Query(ge=0, le=100),
    confidence_threshold: float = Query(default=45, ge=0, le=100),
):
    try:
        items = (
            app.state.match_intelligence_service
            .generate_alerts(
                club_id=club_id,
                prediction_id=prediction_id,
                data_quality_score=data_quality_score,
                confidence_threshold=confidence_threshold,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        "items": [
            item.__dict__
            for item in items
        ]
    }

@app.get("/mvp/intelligence/{club_id}/alerts")
def list_prediction_alerts(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.match_intelligence_service
                .repository.list_alerts(club_id)
            )
        ]
    }

@app.post("/mvp/intelligence/predictions/{prediction_id}/review")
def review_match_prediction(
    prediction_id: str,
    decision_id: str,
    club_id: str,
    status: str,
    reviewer: str,
    note: str = Query(default=""),
):
    try:
        return (
            app.state.match_intelligence_service
            .review_prediction(
                decision_id=decision_id,
                prediction_id=prediction_id,
                club_id=club_id,
                status=status,
                reviewer=reviewer,
                note=note,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/intelligence/predictions/{prediction_id}/decision-report")
def create_match_decision_report(
    prediction_id: str,
    report_id: str,
    club_id: str,
    data_quality_score: float = Query(ge=0, le=100),
):
    try:
        item = (
            app.state.match_intelligence_service
            .decision_report(
                report_id=report_id,
                prediction_id=prediction_id,
                club_id=club_id,
                data_quality_score=data_quality_score,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "key_factors": list(item.key_factors),
        "key_risks": list(item.key_risks),
        "tactical_focus": list(item.tactical_focus),
    }


@app.post("/mvp/intelligence/{club_id}/benchmark")
def benchmark_match_prediction_models(
    club_id: str,
    benchmark_id: str,
):
    try:
        return (
            app.state.match_intelligence_service
            .benchmark_models(
                benchmark_id=benchmark_id,
                club_id=club_id,
            )
            .__dict__
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/intelligence/{club_id}/reliability")
def match_prediction_reliability(
    club_id: str,
    report_id: str,
):
    item = (
        app.state.match_intelligence_service
        .reliability_report(
            report_id=report_id,
            club_id=club_id,
        )
    )
    return {
        **item.__dict__,
        "buckets": list(item.buckets),
    }

@app.post("/mvp/intelligence/predictions/{prediction_id}/audit")
def add_prediction_audit_event(
    prediction_id: str,
    event_id: str,
    club_id: str,
    event_type: str,
    actor: str,
    details: str = Query(default=""),
):
    try:
        return (
            app.state.match_intelligence_service
            .record_audit_event(
                event_id=event_id,
                prediction_id=prediction_id,
                club_id=club_id,
                event_type=event_type,
                actor=actor,
                details=details,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.get("/mvp/intelligence/predictions/{prediction_id}/audit")
def list_prediction_audit_events(
    prediction_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.match_intelligence_service
                .repository.list_audit_events(
                    prediction_id
                )
            )
        ]
    }

@app.get("/mvp/intelligence/predictions/{prediction_id}/shareable-report")
def shareable_match_prediction_report(
    prediction_id: str,
    club_id: str,
    data_quality_score: float = Query(ge=0, le=100),
):
    try:
        return (
            app.state.match_intelligence_service
            .shareable_report(
                prediction_id=prediction_id,
                club_id=club_id,
                data_quality_score=data_quality_score,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@app.post("/mvp/intelligence/predictions/{prediction_id}/learn")
def post_match_prediction_learning(
    prediction_id: str,
    learning_id: str,
    club_id: str,
    actual_home_goals: int = Query(ge=0),
    actual_away_goals: int = Query(ge=0),
):
    try:
        item = (
            app.state.match_intelligence_service
            .post_match_learning(
                learning_id=learning_id,
                prediction_id=prediction_id,
                club_id=club_id,
                actual_home_goals=actual_home_goals,
                actual_away_goals=actual_away_goals,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "root_causes": list(item.root_causes),
        "recommended_actions": list(
            item.recommended_actions
        ),
    }

@app.post("/mvp/intelligence/{club_id}/opponent-memory/rebuild")
def rebuild_match_opponent_memory(
    club_id: str,
):
    items = (
        app.state.match_intelligence_service
        .rebuild_opponent_memory(club_id=club_id)
    )
    return {
        "items": [
            item.__dict__
            for item in items
        ]
    }

@app.get("/mvp/intelligence/{club_id}/opponent-memory")
def list_match_opponent_memory(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.match_intelligence_service
                .repository.list_opponent_memories(
                    club_id
                )
            )
        ]
    }

@app.get("/mvp/intelligence/{club_id}/matches/{match_id}/similar")
def list_similar_historical_matches(
    club_id: str,
    match_id: str,
    limit: int = Query(default=5, ge=1, le=20),
):
    try:
        items = (
            app.state.match_intelligence_service
            .similar_matches(
                club_id=club_id,
                match_id=match_id,
                limit=limit,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return {
        "items": [
            item.__dict__
            for item in items
        ]
    }

@app.get("/mvp/intelligence/{club_id}/recalibration-recommendation")
def match_recalibration_recommendation(
    club_id: str,
):
    return (
        app.state.match_intelligence_service
        .recalibration_recommendation(
            club_id=club_id
        )
    )


@app.post("/mvp/intelligence/{club_id}/opponent-profile/history")
def derive_opponent_profile_from_history(
    club_id: str,
    profile_id: str,
    opponent_name: str,
    cutoff_at: int,
):
    return (
        app.state.match_intelligence_service
        .derive_opponent_profile_from_history(
            profile_id=profile_id,
            club_id=club_id,
            opponent_name=opponent_name,
            cutoff_at=cutoff_at,
        )
        .__dict__
    )

@app.post("/mvp/intelligence/{club_id}/walk-forward")
def walk_forward_match_backtest(
    club_id: str,
    report_id: str,
    competition: str,
    warmup_matches: int = Query(default=5, ge=3, le=30),
):
    try:
        return (
            app.state.match_intelligence_service
            .walk_forward_backtest(
                report_id=report_id,
                club_id=club_id,
                competition=competition,
                warmup_matches=warmup_matches,
            )
            .__dict__
        )
    except MatchIntelligenceValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/intelligence/predictions/{prediction_id}/reproducibility")
def create_prediction_reproducibility_record(
    prediction_id: str,
    record_id: str,
    model_version: str = Query(default="build-014"),
):
    try:
        return (
            app.state.match_intelligence_service
            .reproducibility_record(
                record_id=record_id,
                prediction_id=prediction_id,
                model_version=model_version,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.post("/mvp/intelligence/{club_id}/season-report")
def create_season_prediction_performance_report(
    club_id: str,
    report_id: str,
    competition: str,
    season_key: str,
):
    return (
        app.state.match_intelligence_service
        .season_performance_report(
            report_id=report_id,
            club_id=club_id,
            competition=competition,
            season_key=season_key,
        )
        .__dict__
    )


@app.post("/mvp/intelligence/{club_id}/release-gate")
def run_release_gate(
    club_id: str,
    gate_id: str,
    model_version: str = Query(default="build-015"),
    tests_passed: bool = Query(default=True),
    documentation_ready: bool = Query(default=True),
):
    item = (
        app.state.match_intelligence_service
        .release_gate(
            gate_id=gate_id,
            club_id=club_id,
            model_version=model_version,
            tests_passed=tests_passed,
            documentation_ready=documentation_ready,
        )
    )
    return {
        **item.__dict__,
        "blockers": list(item.blockers),
        "warnings": list(item.warnings),
    }

@app.post("/mvp/intelligence/{club_id}/pipeline/run")
def run_full_match_prediction_pipeline(
    club_id: str,
    run_id: str,
    match_id: str,
    club_profile_id: str,
    opponent_profile_id: str,
    reviewer: str = Query(default="system"),
):
    try:
        return (
            app.state.match_intelligence_service
            .run_end_to_end_pipeline(
                run_id=run_id,
                club_id=club_id,
                match_id=match_id,
                club_profile_id=club_profile_id,
                opponent_profile_id=opponent_profile_id,
                reviewer=reviewer,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.get("/mvp/intelligence/{club_id}/pipeline/runs")
def list_full_pipeline_runs(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.match_intelligence_service
                .repository.list_pipeline_runs(
                    club_id
                )
            )
        ]
    }

@app.post("/mvp/intelligence/{club_id}/pilot-readiness")
def create_pilot_readiness_report(
    club_id: str,
    report_id: str,
    documentation_ready: bool = Query(default=True),
):
    item = (
        app.state.match_intelligence_service
        .pilot_readiness(
            report_id=report_id,
            club_id=club_id,
            documentation_ready=documentation_ready,
        )
    )
    return {
        **item.__dict__,
        "action_items": list(item.action_items),
    }


@app.get("/mvp/stabilization/security")
def stabilization_security_report(
    report_id: str,
    environment: str | None = None,
):
    item = (
        app.state.pilot_stabilization_service
        .security_report(
            report_id=report_id,
            environment=environment,
        )
    )
    return {
        **item.__dict__,
        "blockers": list(item.blockers),
        "warnings": list(item.warnings),
    }

@app.post("/mvp/stabilization/{club_id}/backup")
def create_club_backup(
    club_id: str,
    backup_id: str,
):
    try:
        item = (
            app.state.pilot_stabilization_service
            .create_backup(
                backup_id=backup_id,
                club_id=club_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    return item.__dict__

@app.post("/mvp/stabilization/restore/validate")
def validate_club_restore(
    validation_id: str,
    backup_id: str,
    payload_json: str,
    expected_checksum: str,
):
    item = (
        app.state.pilot_stabilization_service
        .validate_restore(
            validation_id=validation_id,
            backup_id=backup_id,
            payload_json=payload_json,
            expected_checksum=expected_checksum,
        )
    )
    return {
        **item.__dict__,
        "errors": list(item.errors),
    }

@app.get("/mvp/stabilization/contract")
def create_api_contract_snapshot(
    snapshot_id: str,
):
    routes = tuple(
        sorted(
            route.path
            for route in app.routes
            if hasattr(route, "path")
        )
    )
    item = (
        app.state.pilot_stabilization_service
        .contract_snapshot(
            snapshot_id=snapshot_id,
            api_version="build-024-supply-chain",
            routes=routes,
        )
    )
    return {
        **item.__dict__,
        "routes": list(item.routes),
    }

@app.get("/mvp/stabilization/smoke")
def stabilization_smoke_test():
    return {
        "api": "ok",
        "workspace": (
            app.state.mvp_workspace_service
            is not None
        ),
        "auth": (
            app.state.mvp_auth_service
            is not None
        ),
        "integrations": (
            app.state.mvp_integration_service
            is not None
        ),
        "intelligence": (
            app.state.match_intelligence_service
            is not None
        ),
        "stabilization": (
            app.state.pilot_stabilization_service
            is not None
        ),
        "version": "build-016",
    }


@app.post("/mvp/observability/{club_id}/events")
def record_pilot_telemetry_event(
    club_id: str,
    event_id: str,
    category: str,
    severity: str,
    component: str,
    message: str,
    duration_ms: int = Query(default=0, ge=0),
):
    try:
        return (
            app.state.pilot_observability_service
            .record_event(
                event_id=event_id,
                club_id=club_id,
                category=category,
                severity=severity,
                component=component,
                message=message,
                duration_ms=duration_ms,
            )
            .__dict__
        )
    except ObservabilityValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/observability/{club_id}/events")
def list_pilot_telemetry_events(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.pilot_observability_service
                .repository.list_events(club_id)
            )
        ]
    }

@app.post("/mvp/observability/{club_id}/incidents")
def open_pilot_incident(
    club_id: str,
    incident_id: str,
    title: str,
    severity: str,
    component: str,
    owner: str,
    description: str = Query(default=""),
):
    try:
        return (
            app.state.pilot_observability_service
            .open_incident(
                incident_id=incident_id,
                club_id=club_id,
                title=title,
                severity=severity,
                component=component,
                owner=owner,
                description=description,
            )
            .__dict__
        )
    except ObservabilityValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/observability/incidents/{incident_id}")
def update_pilot_incident(
    incident_id: str,
    status: str,
    owner: str | None = None,
):
    try:
        return (
            app.state.pilot_observability_service
            .update_incident(
                incident_id=incident_id,
                status=status,
                owner=owner,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ObservabilityValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/observability/{club_id}/incidents")
def list_pilot_incidents(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.pilot_observability_service
                .repository.list_incidents(club_id)
            )
        ]
    }

@app.get("/mvp/observability/{club_id}/health-score")
def pilot_health_score(
    club_id: str,
    report_id: str,
):
    return (
        app.state.pilot_observability_service
        .health_score(
            report_id=report_id,
            club_id=club_id,
        )
        .__dict__
    )

@app.post("/mvp/observability/{club_id}/alarms")
def generate_pilot_alarm_events(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.pilot_observability_service
                .generate_alarm_events(
                    club_id=club_id
                )
            )
        ]
    }

@app.get("/mvp/observability/{club_id}/daily-summary")
def pilot_daily_summary(
    club_id: str,
    summary_id: str,
    day_key: str,
):
    return (
        app.state.pilot_observability_service
        .daily_summary(
            summary_id=summary_id,
            club_id=club_id,
            day_key=day_key,
        )
        .__dict__
    )


@app.post("/mvp/product-analytics/{club_id}/usage")
def record_product_usage_event(
    club_id: str,
    event_id: str,
    user_id: str,
    feature: str,
    action: str,
    session_id: str,
    duration_ms: int = Query(default=0, ge=0),
    success: bool = Query(default=True),
):
    try:
        return (
            app.state.pilot_product_analytics_service
            .record_usage(
                event_id=event_id,
                club_id=club_id,
                user_id=user_id,
                feature=feature,
                action=action,
                session_id=session_id,
                duration_ms=duration_ms,
                success=success,
            )
            .__dict__
        )
    except ProductAnalyticsValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/product-analytics/{club_id}/usage")
def list_product_usage_events(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.pilot_product_analytics_service
                .repository.list_usage(club_id)
            )
        ]
    }

@app.post("/mvp/product-analytics/{club_id}/feedback")
def submit_pilot_feedback(
    club_id: str,
    feedback_id: str,
    user_id: str,
    feature: str,
    rating: int = Query(ge=1, le=5),
    category: str = Query(default="OTHER"),
    message: str = Query(default=""),
):
    try:
        return (
            app.state.pilot_product_analytics_service
            .submit_feedback(
                feedback_id=feedback_id,
                club_id=club_id,
                user_id=user_id,
                feature=feature,
                rating=rating,
                category=category,
                message=message,
            )
            .__dict__
        )
    except ProductAnalyticsValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/product-analytics/{club_id}/feedback")
def list_pilot_feedback(
    club_id: str,
):
    return {
        "items": [
            item.__dict__
            for item in (
                app.state.pilot_product_analytics_service
                .repository.list_feedback(club_id)
            )
        ]
    }

@app.get("/mvp/product-analytics/{club_id}/adoption")
def product_feature_adoption_report(
    club_id: str,
    report_id: str,
):
    item = (
        app.state.pilot_product_analytics_service
        .adoption_report(
            report_id=report_id,
            club_id=club_id,
        )
    )
    return {
        **item.__dict__,
        "feature_usage": list(item.feature_usage),
    }

@app.get("/mvp/product-analytics/{club_id}/priorities")
def product_improvement_priorities(
    club_id: str,
):
    return {
        "items": [
            {
                **item.__dict__,
                "reasons": list(item.reasons),
            }
            for item in (
                app.state.pilot_product_analytics_service
                .improvement_priorities(
                    club_id=club_id
                )
            )
        ]
    }

@app.get("/mvp/product-analytics/{club_id}/weekly")
def weekly_pilot_product_report(
    club_id: str,
    report_id: str,
    week_key: str,
):
    item = (
        app.state.pilot_product_analytics_service
        .weekly_report(
            report_id=report_id,
            club_id=club_id,
            week_key=week_key,
        )
    )
    return {
        **item.__dict__,
        "top_priorities": list(item.top_priorities),
    }


@app.post("/mvp/experiments/{club_id}/flags")
def create_feature_flag(
    club_id: str,
    flag_id: str,
    name: str,
    enabled: bool = Query(default=True),
    rollout_percentage: int = Query(default=100, ge=0, le=100),
    allowed_roles: str = Query(default=""),
    variant: str = Query(default="default"),
):
    try:
        item = (
            app.state.pilot_experiment_service
            .create_flag(
                flag_id=flag_id,
                club_id=club_id,
                name=name,
                enabled=enabled,
                rollout_percentage=rollout_percentage,
                allowed_roles=tuple(
                    token.strip()
                    for token in allowed_roles.split(",")
                    if token.strip()
                ),
                variant=variant,
            )
        )
    except ExperimentValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "allowed_roles": list(item.allowed_roles),
    }

@app.get("/mvp/experiments/flags/{flag_id}/evaluate")
def evaluate_feature_flag(
    flag_id: str,
    user_id: str,
    role: str,
):
    try:
        return (
            app.state.pilot_experiment_service
            .evaluate_flag(
                flag_id=flag_id,
                user_id=user_id,
                role=role,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.get("/mvp/experiments/{club_id}/flags")
def list_feature_flags(
    club_id: str,
):
    return {
        "items": [
            {
                **item.__dict__,
                "allowed_roles": list(item.allowed_roles),
            }
            for item in (
                app.state.pilot_experiment_service
                .repository.list_flags(club_id)
            )
        ]
    }

@app.post("/mvp/experiments/{club_id}")
def create_pilot_experiment(
    club_id: str,
    experiment_id: str,
    name: str,
    feature: str,
    control_variant: str,
    treatment_variant: str,
    rollout_percentage: int = Query(default=50, ge=1, le=100),
    primary_metric: str = Query(default="success_rate"),
    status: str = Query(default="DRAFT"),
):
    try:
        return (
            app.state.pilot_experiment_service
            .create_experiment(
                experiment_id=experiment_id,
                club_id=club_id,
                name=name,
                feature=feature,
                control_variant=control_variant,
                treatment_variant=treatment_variant,
                rollout_percentage=rollout_percentage,
                primary_metric=primary_metric,
                status=status,
            )
            .__dict__
        )
    except ExperimentValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/experiments/{experiment_id}/status")
def update_pilot_experiment_status(
    experiment_id: str,
    status: str,
):
    try:
        return (
            app.state.pilot_experiment_service
            .update_experiment_status(
                experiment_id=experiment_id,
                status=status,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ExperimentValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/experiments/{experiment_id}/assign")
def assign_experiment_variant(
    experiment_id: str,
    assignment_id: str,
    club_id: str,
    user_id: str,
):
    try:
        return (
            app.state.pilot_experiment_service
            .assign_variant(
                assignment_id=assignment_id,
                experiment_id=experiment_id,
                club_id=club_id,
                user_id=user_id,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ExperimentValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/experiments/{experiment_id}/metrics")
def record_experiment_metric(
    experiment_id: str,
    metric_id: str,
    club_id: str,
    user_id: str,
    variant: str,
    metric_name: str,
    metric_value: float,
    success: bool = Query(default=True),
):
    try:
        return (
            app.state.pilot_experiment_service
            .record_metric(
                metric_id=metric_id,
                experiment_id=experiment_id,
                club_id=club_id,
                user_id=user_id,
                variant=variant,
                metric_name=metric_name,
                metric_value=metric_value,
                success=success,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except ExperimentValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.get("/mvp/experiments/{experiment_id}/report")
def pilot_experiment_report(
    experiment_id: str,
    report_id: str,
):
    try:
        return (
            app.state.pilot_experiment_service
            .report(
                report_id=report_id,
                experiment_id=experiment_id,
            )
            .__dict__
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

@app.post("/mvp/experiments/{experiment_id}/rollback")
def rollback_pilot_experiment(
    experiment_id: str,
    flag_id: str | None = None,
):
    try:
        return (
            app.state.pilot_experiment_service
            .rollback_experiment(
                experiment_id=experiment_id,
                flag_id=flag_id,
            )
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc


@app.post("/mvp/final-pilot/{club_id}/seed")
def seed_final_pilot_demo(
    club_id: str,
):
    return (
        app.state.final_pilot_service
        .seed_final_demo(club_id=club_id)
    )

@app.post("/mvp/final-pilot/{club_id}/run")
def run_final_pilot_package(
    club_id: str,
    report_id: str,
    reviewer: str = Query(default="system"),
):
    item = (
        app.state.final_pilot_service
        .run_final_pilot(
            report_id=report_id,
            club_id=club_id,
            reviewer=reviewer,
        )
    )
    return {
        **item.__dict__,
        "blockers": list(item.blockers),
    }


@app.post("/mvp/pilot-acceptance/{club_id}/run")
def run_pilot_acceptance(
    club_id: str,
    report_id: str,
    reviewer: str = Query(default="acceptance-bot"),
):
    item = (
        app.state.pilot_acceptance_service
        .run_acceptance(
            report_id=report_id,
            club_id=club_id,
            reviewer=reviewer,
        )
    )
    return {
        **item.__dict__,
        "checks": list(item.checks),
    }

@app.get("/mvp/pilot-acceptance/{club_id}/repeatability")
def check_final_pilot_repeatability(
    club_id: str,
):
    return (
        app.state.pilot_acceptance_service
        .repeatability_check(club_id=club_id)
    )


@app.post("/mvp/delivery/import/validate")
def validate_delivery_import(
    report_id: str,
    import_type: str,
    csv_text: str,
):
    try:
        item = (
            app.state.delivery_hardening_service
            .validate_csv(
                report_id=report_id,
                import_type=import_type,
                csv_text=csv_text,
            )
        )
    except DeliveryHardeningValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "valid_payload": list(item.valid_payload),
        "quarantine_payload": list(item.quarantine_payload),
        "issues": list(item.issues),
    }


@app.get("/mvp/release-freeze/preflight")
def release_freeze_preflight(
    report_id: str,
    database_ready: bool = Query(default=True),
    redis_ready: bool = Query(default=True),
    backup_ready: bool = Query(default=True),
    observability_ready: bool = Query(default=True),
):
    item = (
        app.state.release_freeze_service
        .production_preflight(
            report_id=report_id,
            database_ready=database_ready,
            redis_ready=redis_ready,
            backup_ready=backup_ready,
            observability_ready=observability_ready,
        )
    )
    return {
        **item.__dict__,
        "required_variables": list(item.required_variables),
        "missing_variables": list(item.missing_variables),
        "insecure_variables": list(item.insecure_variables),
    }

@app.post("/mvp/release-freeze/migration")
def release_freeze_migration_preflight(
    report_id: str,
    source_schema: str,
    target_schema: str,
    source_fields: str,
    target_fields: str,
):
    item = (
        app.state.release_freeze_service
        .migration_preflight(
            report_id=report_id,
            source_schema=source_schema,
            target_schema=target_schema,
            source_fields=tuple(
                token.strip()
                for token in source_fields.split(",")
                if token.strip()
            ),
            target_fields=tuple(
                token.strip()
                for token in target_fields.split(",")
                if token.strip()
            ),
        )
    )
    return {
        **item.__dict__,
        "destructive_changes": list(item.destructive_changes),
        "warnings": list(item.warnings),
    }

@app.post("/mvp/release-freeze/sign")
def sign_release_manifest(
    manifest_id: str,
    build_version: str,
    package_checksum: str,
    source_manifest_checksum: str,
    acceptance_fingerprint: str,
    signing_key: str,
):
    try:
        return (
            app.state.release_freeze_service
            .sign_release(
                manifest_id=manifest_id,
                build_version=build_version,
                package_checksum=package_checksum,
                source_manifest_checksum=source_manifest_checksum,
                acceptance_fingerprint=acceptance_fingerprint,
                signing_key=signing_key,
            )
            .__dict__
        )
    except ReleaseFreezeValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.post("/mvp/supply-chain/sbom")
def create_supply_chain_sbom(
    report_id: str,
    build_version: str,
    dependencies_json: str,
):
    try:
        dependencies = tuple(
            json.loads(dependencies_json)
        )
        item = (
            app.state.supply_chain_security_service
            .sbom_report(
                report_id=report_id,
                build_version=build_version,
                dependencies=dependencies,
            )
        )
    except (ValueError, TypeError, SupplyChainValidationError) as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "dependencies": list(item.dependencies),
    }

@app.post("/mvp/supply-chain/reproducible-build")
def verify_reproducible_build(
    report_id: str,
    first_manifest_json: str,
    second_manifest_json: str,
):
    try:
        first = json.loads(first_manifest_json)
        second = json.loads(second_manifest_json)
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail="Manifest JSON geçersiz",
        ) from exc
    return (
        app.state.supply_chain_security_service
        .reproducible_build_report(
            report_id=report_id,
            first_manifest=first,
            second_manifest=second,
        )
        .__dict__
    )


@app.post("/mvp/real-data/dataset-report")
def create_real_data_dataset_report(
    report_id: str,
    competition: str,
    season: str,
    csv_text: str,
):
    try:
        item = (
            app.state.real_data_training_service
            .dataset_report(
                report_id=report_id,
                csv_text=csv_text,
                competition=competition,
                season=season,
            )
        )
    except RealDataValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "feature_names": list(item.feature_names),
    }

@app.post("/mvp/real-data/train-baseline")
def train_real_data_baseline(
    model_id: str,
    competition: str,
    csv_text: str,
    validation_fraction: float = Query(default=0.25, ge=0.10, le=0.40),
):
    try:
        return (
            app.state.real_data_training_service
            .train_baseline(
                model_id=model_id,
                csv_text=csv_text,
                competition=competition,
                validation_fraction=validation_fraction,
            )
            .__dict__
        )
    except RealDataValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.post("/mvp/ensemble/train")
def train_ensemble_model(
    model_id: str,
    competition: str,
    csv_text: str,
    validation_fraction: float = Query(default=0.25, ge=0.10, le=0.40),
):
    try:
        return (
            app.state.ensemble_training_service
            .train(
                model_id=model_id,
                csv_text=csv_text,
                competition=competition,
                validation_fraction=validation_fraction,
            )
            .__dict__
        )
    except RealDataValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

@app.post("/mvp/ensemble/walk-forward")
def ensemble_walk_forward(
    report_id: str,
    competition: str,
    csv_text: str,
    minimum_train_size: int = Query(default=20, ge=20),
    step_size: int = Query(default=5, ge=1, le=20),
):
    try:
        return (
            app.state.ensemble_training_service
            .walk_forward_backtest(
                report_id=report_id,
                csv_text=csv_text,
                competition=competition,
                minimum_train_size=minimum_train_size,
                step_size=step_size,
            )
            .__dict__
        )
    except RealDataValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


@app.post("/mvp/rolling-model/train")
def train_rolling_team_model(
    model_id: str,
    competition: str,
    csv_text: str,
    validation_fraction: float = Query(default=0.25, ge=0.10, le=0.40),
):
    try:
        item = (
            app.state.rolling_team_model_service
            .train(
                model_id=model_id,
                csv_text=csv_text,
                competition=competition,
                validation_fraction=validation_fraction,
            )
        )
    except RealDataValidationError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    return {
        **item.__dict__,
        "feature_names": list(item.feature_names),
        "means": list(item.means),
        "scales": list(item.scales),
        "weights": [list(row) for row in item.weights],
        "biases": list(item.biases),
    }


@app.post("/mvp/mobile/quick-predict")
def mobile_quick_predict(payload: MobileQuickPredictionRequest):
    model_path = (
        Path(__file__).resolve().parents[3]
        / "QUICK_ENSEMBLE_MODEL.json"
    )
    if not model_path.exists():
        raise HTTPException(
            status_code=503,
            detail="Quick model bulunamadı",
        )
    model = EnsembleModel(
        **json.loads(
            model_path.read_text(encoding="utf-8")
        )
    )
    result = (
        app.state.ensemble_training_service
        .predict(
            model=model,
            home_xg=payload.home_xg,
            away_xg=payload.away_xg,
            home_elo=payload.home_elo,
            away_elo=payload.away_elo,
            home_form=payload.home_form,
            away_form=payload.away_form,
        )
    )
    return {
        "match": f"{payload.home_team} - {payload.away_team}",
        **result,
    }


@app.get("/health")
def health(request: Request):
    return {
        "status": (
            "shutting_down"
            if getattr(
                request.app.state,
                "shutting_down",
                False,
            )
            else "ok"
        ),
        "environment": settings.environment,
        "repository": (
            event_repository
            .__class__
            .__name__
        ),
    }

@app.get("/ready")
def readiness(request: Request):
    drain_controller = request.app.state.drain_controller
    if drain_controller.enabled:
        return {
            "ready": False,
            "checks": {
                "drain": {
                    "ok": False,
                    "detail": drain_controller.reason,
                }
            },
        }

    if getattr(
        request.app.state,
        "shutting_down",
        False,
    ):
        return {
            "ready": False,
            "checks": {
                "shutdown": {
                    "ok": False,
                    "detail": "shutting_down",
                }
            },
        }

    database_ok, database_detail = (
        database_ready()
    )
    provider_ok, provider_detail = (
        provider_ready()
    )
    maintenance = request.app.state.maintenance_controller
    runtime_checks = (
        ReadinessCheck(
            name="database",
            ok=database_ok,
            critical=True,
            detail=database_detail,
        ),
        ReadinessCheck(
            name="sportmonks",
            ok=(
                provider_ok
                or settings.environment
                in {"test", "development"}
            ),
            critical=True,
            detail=provider_detail,
        ),
        ReadinessCheck(
            name="maintenance",
            ok=not maintenance.enabled,
            critical=True,
            detail=(
                "disabled"
                if not maintenance.enabled
                else maintenance.reason or "enabled"
            ),
        ),
    )
    report = (
        request.app.state
        .production_readiness_validator
        .build_report(
            runtime_checks=runtime_checks
        )
    )
    return {
        "ready": report.ready,
        "environment": report.environment,
        "configuration_fingerprint": (
            report.configuration_fingerprint
        ),
        "checks": {
            item.name: {
                "ok": item.ok,
                "critical": item.critical,
                "detail": item.detail,
            }
            for item in report.checks
        },
    }

@app.get(
    "/metrics",
    response_class=PlainTextResponse,
)
def prometheus_metrics(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return metrics.render()

@app.get("/audit")
def audit_events(
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    subject: str | None = None,
    resource: str | None = None,
    outcome: str | None = None,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    return [
        item.__dict__
        for item
        in app.state.audit_repository.list(
            limit=limit,
            offset=offset,
            subject=subject,
            resource=resource,
            outcome=outcome,
        )
    ]

@app.post("/auth/dev-token")
def dev_token(request: Request):
    if settings.environment not in {"test", "development"}:
        raise HTTPException(status_code=404, detail="Bulunamadı")
    access_token = app.state.token_service.issue_access_token(
        subject="developer",
        roles=("admin", "ops", "analyst"),
        ttl_seconds=900,
    )
    refresh_token, session = app.state.refresh_sessions.issue(
        subject="developer",
        roles=("admin", "ops", "analyst"),
        user_agent=request.headers.get("User-Agent"),
        ip_address=(
            request.client.host
            if request.client
            else None
        ),
    )
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "refresh_session_id": session.session_id,
        "token_type": "bearer",
        "expires_in": 900,
    }

@app.post("/auth/refresh")
def refresh_access_token(
    request: Request,
    refresh_token: str = Query(min_length=20),
):
    try:
        rotated, session = app.state.refresh_sessions.rotate(
            refresh_token,
            user_agent=request.headers.get("User-Agent"),
            ip_address=(
                request.client.host
                if request.client
                else None
            ),
        )
    except RefreshReuseDetected as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    return {
        "access_token": app.state.token_service.issue_access_token(
            subject=session.subject,
            roles=session.roles,
            ttl_seconds=900,
        ),
        "refresh_token": rotated,
        "refresh_session_id": session.session_id,
        "rotation": session.rotation,
        "token_type": "bearer",
        "expires_in": 900,
    }






@app.post("/admin/session-index-progress/reset")
def reset_session_index_progress(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    worker = app.state.session_maintenance_worker
    if (
        worker is None
        or worker.maintainer.progress_repository is None
    ):
        return {
            "enabled": False,
            "progress": None,
        }

    fencing_token = int(
        getattr(
            worker.lease,
            "fencing_token",
            0,
        )
    )
    if fencing_token <= 0:
        raise HTTPException(
            status_code=409,
            detail=(
                "Progress reset için aktif bakım "
                "lease'i gerekli"
            ),
        )

    progress = (
        worker
        .maintainer
        .progress_repository
        .reset(
            fencing_token=fencing_token
        )
    )
    return {
        "enabled": True,
        "progress": progress.__dict__,
    }






@app.post("/admin/session-maintenance-quarantine/{claim_id}/verify")
def verify_quarantined_index(
    claim_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.session_maintenance_worker
    service = app.state.quarantine_verification_service
    if worker is None or service is None:
        raise HTTPException(
            status_code=409,
            detail="Karantina doğrulama etkin değil",
        )

    fencing_token = int(
        getattr(worker.lease, "fencing_token", 0)
    )
    if fencing_token <= 0:
        raise HTTPException(
            status_code=409,
            detail="Aktif bakım lease'i gerekli",
        )

    try:
        evidence = service.retry_and_verify(
            claim_id=claim_id,
            operator=principal.subject,
            fencing_token=fencing_token,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_quarantine_verification_success_total"
        if evidence.verified
        else "aslan_quarantine_verification_failure_total"
    )
    return evidence.__dict__


@app.post("/admin/session-maintenance-quarantine/{claim_id}/close-request")
def request_verified_quarantine_close(
    claim_id: str,
    note: str = Query(min_length=3, max_length=1000),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    service = app.state.dual_control_closure_service
    if service is None:
        raise HTTPException(
            status_code=409,
            detail="Çift onaylı kapatma etkin değil",
        )

    request_item = service.request_close(
        claim_id=claim_id,
        requested_by=principal.subject,
        note=note,
    )
    metrics.increment(
        "aslan_quarantine_close_requests_total"
    )
    return request_item.__dict__



@app.get("/admin/session-maintenance-quarantine/{claim_id}/risk-policy")
def quarantine_risk_policy(
    claim_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    diagnostics = app.state.quarantine_diagnostics
    journal = (
        app.state
        .session_maintenance_worker
        .maintainer
        .journal
        if app.state.session_maintenance_worker is not None
        else None
    )
    engine = app.state.quorum_risk_policy_engine

    if diagnostics is None or journal is None:
        raise HTTPException(
            status_code=409,
            detail="Risk politikası etkin değil",
        )

    try:
        diagnostic = diagnostics.inspect(claim_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    attempts = 0
    for item in journal.quarantined_indexes():
        if item.claim_id == claim_id:
            attempts = item.attempts
            break

    policy = engine.evaluate(
        orphan_members=diagnostic.orphan_members,
        live_members=diagnostic.live_members,
        index_ttl=diagnostic.index_ttl,
        attempts=attempts,
        phase=diagnostic.phase,
    )
    return policy.__dict__

@app.post("/admin/session-maintenance-quarantine/close-requests/{request_id}/quorum")
def configure_close_request_quorum(
    request_id: str,
    required_approvals: int = Query(ge=1, le=5),
    required_groups: str = Query(default="admin"),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    service = app.state.quorum_closure_service
    if service is None:
        raise HTTPException(
            status_code=409,
            detail="Quorum onayı etkin değil",
        )

    groups = tuple(
        item.strip()
        for item in required_groups.split(",")
        if item.strip()
    )
    policy = service.prepare(
        request_id=request_id,
        required_approvals=required_approvals,
        required_groups=groups,
    )
    return policy.__dict__

@app.post("/admin/session-maintenance-quarantine/close-requests/{request_id}/vote")
async def vote_close_request_quorum(
    request_id: str,
    approve: bool = Query(),
    voter_group: str = Query(min_length=2, max_length=64),
    note: str = Query(min_length=3, max_length=1000),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.session_maintenance_worker
    service = app.state.quorum_closure_service

    if worker is None or service is None:
        raise HTTPException(
            status_code=409,
            detail="Quorum onayı etkin değil",
        )

    fencing_token = int(
        getattr(worker.lease, "fencing_token", 0)
    )
    if approve and fencing_token <= 0:
        raise HTTPException(
            status_code=409,
            detail="Aktif bakım lease'i gerekli",
        )

    try:
        result = await service.vote_and_maybe_close_async(
            request_id=request_id,
            voter=principal.subject,
            group=voter_group,
            voter_roles=principal.roles,
            approve=approve,
            note=note,
            fencing_token=fencing_token,
        )
    except DuplicateVote as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_quarantine_quorum_votes_total"
    )
    if result.closed:
        metrics.increment(
            "aslan_quarantine_quorum_closures_total"
        )
    if result.ownership_lost:
        metrics.increment(
            "aslan_quarantine_quorum_ownership_lost_total"
        )
    return result.__dict__



@app.get("/admin/session-maintenance-quarantine/close-requests/{request_id}/compensations")
def list_quorum_compensations(
    request_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.compensation_repository
    if repository is None:
        return {"enabled": False, "items": []}
    return {
        "enabled": True,
        "items": [
            item.__dict__
            for item in repository.list_request(request_id)
        ],
    }







@app.get("/admin/compensations/outbox/ordering/{partition}")
def get_outbox_ordering_state(
    partition: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.event_ordering_repository
    if repository is None:
        return {"enabled": False, "state": None}
    state = repository.get(partition)
    return {
        "enabled": True,
        "state": state.__dict__ if state is not None else None,
    }

@app.post("/admin/sagas")
def create_saga(saga_type: str = Query(min_length=2, max_length=100), steps: str = Query(min_length=1, max_length=1000), principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops"))):
    repository = app.state.saga_repository
    if repository is None:
        raise HTTPException(status_code=409, detail="Saga orchestrator etkin değil")
    names = tuple(x.strip() for x in steps.split(",") if x.strip())
    if not names:
        raise HTTPException(status_code=422, detail="En az bir saga adımı gerekli")
    item = repository.create(saga_type=saga_type, step_names=names, context={"operator": principal.subject})
    return {**item.__dict__, "steps": [x.__dict__ for x in item.steps]}

@app.get("/admin/sagas/{saga_id}")
def get_saga(saga_id: str, principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops"))):
    repository = app.state.saga_repository
    item = repository.get(saga_id) if repository is not None else None
    if item is None:
        raise HTTPException(status_code=404, detail="Saga bulunamadı")
    return {**item.__dict__, "steps": [x.__dict__ for x in item.steps]}

@app.get("/admin/compensations/outbox/transport/health")
def get_outbox_transport_health(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    breaker = app.state.outbox_circuit_breaker
    if breaker is None:
        return {
            "enabled": False,
            "circuit": None,
        }

    return {
        "enabled": True,
        "circuit": breaker.get().__dict__,
    }

@app.post("/admin/compensations/outbox/transport/circuit/reset")
def reset_outbox_transport_circuit(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    breaker = app.state.outbox_circuit_breaker
    if breaker is None:
        raise HTTPException(
            status_code=409,
            detail="Outbox circuit breaker etkin değil",
        )

    state = breaker.reset()
    metrics.increment(
        "aslan_outbox_circuit_resets_total"
    )
    return state.__dict__

@app.get("/admin/compensations/outbox/{event_id}/receipt")
def get_outbox_receipt(
    event_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.outbox_receipt_repository
    if repository is None:
        return {
            "enabled": False,
            "receipt": None,
        }

    receipt = repository.get(event_id)
    return {
        "enabled": True,
        "receipt": (
            receipt.__dict__
            if receipt is not None
            else None
        ),
    }

@app.get("/admin/compensations/outbox/{event_id}/delivery")
def get_outbox_delivery(
    event_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.outbox_delivery_repository
    if repository is None:
        return {
            "enabled": False,
            "delivery": None,
        }

    record = repository.get(event_id)
    return {
        "enabled": True,
        "delivery": (
            record.__dict__
            if record is not None
            else None
        ),
    }

@app.post("/admin/compensations/outbox/publish")
async def publish_compensation_outbox(
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.outbox_publisher_worker
    if worker is None:
        raise HTTPException(
            status_code=409,
            detail="Outbox publisher etkin değil",
        )

    results = await worker.publisher.publish_batch_async(limit=limit)
    metrics.increment(
        "aslan_compensation_outbox_publish_cycles_total"
    )
    return {
        "items": [
            item.__dict__
            for item in results
        ],
    }

@app.get("/admin/compensations/outbox")
def list_compensation_outbox(
    limit: int = Query(default=100, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    committer = app.state.compensation_committer
    if committer is None:
        return {"enabled": False, "items": []}
    return {
        "enabled": True,
        "items": [
            item.__dict__
            for item in committer.list_events(limit=limit)
        ],
    }

@app.get("/admin/compensations/{compensation_id}/execution")
def get_compensation_execution(
    compensation_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.compensation_execution_repository
    if repository is None:
        return {
            "enabled": False,
            "execution": None,
        }

    record = repository.get(compensation_id)
    return {
        "enabled": True,
        "execution": (
            record.__dict__
            if record is not None
            else None
        ),
    }

@app.post("/admin/compensations/{compensation_id}/execute")
async def execute_compensation(
    compensation_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.compensation_worker
    if worker is None:
        raise HTTPException(
            status_code=409,
            detail="Compensation worker etkin değil",
        )

    try:
        result = await asyncio.to_thread(
            worker.orchestrator.execute,
            compensation_id,
        )
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_compensation_execution_total"
    )
    if result.status == "DEAD_LETTER":
        metrics.increment(
            "aslan_compensation_dead_letter_total"
        )
    if result.ownership_lost:
        metrics.increment(
            "aslan_compensation_ownership_lost_total"
        )
    return result.__dict__

@app.post("/admin/compensations/{compensation_id}/requeue")
def requeue_compensation(
    compensation_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    repository = app.state.compensation_repository
    if repository is None:
        raise HTTPException(
            status_code=409,
            detail="Compensation yönetimi etkin değil",
        )

    record = repository.get(compensation_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Compensation kaydı bulunamadı",
        )

    updated = repository.requeue(record)
    metrics.increment(
        "aslan_compensation_requeued_total"
    )
    return updated.__dict__

@app.get("/admin/compensations/due")
def list_due_compensations(
    limit: int = Query(default=50, ge=1, le=500),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.compensation_repository
    if repository is None:
        return {"enabled": False, "items": []}

    return {
        "enabled": True,
        "items": [
            item.__dict__
            for item in repository.list_due(limit=limit)
        ],
    }

@app.get("/admin/session-maintenance-quarantine/close-requests/{request_id}/execution")
def get_quorum_execution(
    request_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.quorum_execution_repository
    if repository is None:
        return {
            "enabled": False,
            "execution": None,
        }

    record = repository.get(request_id)
    return {
        "enabled": True,
        "execution": (
            record.__dict__
            if record is not None
            else None
        ),
    }

@app.get("/admin/session-maintenance-quarantine/close-requests/{request_id}/quorum")
def get_close_request_quorum(
    request_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.quorum_approval_repository
    if repository is None:
        return {
            "enabled": False,
            "decision": None,
            "votes": [],
            "integrity_valid": False,
        }

    try:
        decision = repository.decision(request_id)
        votes = repository.list_votes(request_id)
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    return {
        "enabled": True,
        "decision": decision.__dict__,
        "votes": [
            vote.__dict__
            for vote in votes
        ],
        "integrity_valid": (
            repository.verify_votes(request_id)
        ),
    }

@app.post("/admin/session-maintenance-quarantine/close-requests/{request_id}/decision")
def decide_verified_quarantine_close(
    request_id: str,
    approve: bool = Query(),
    decision_note: str = Query(
        min_length=3,
        max_length=1000,
    ),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    worker = app.state.session_maintenance_worker
    service = app.state.dual_control_closure_service

    if worker is None or service is None:
        raise HTTPException(
            status_code=409,
            detail="Çift onaylı kapatma etkin değil",
        )

    fencing_token = int(
        getattr(worker.lease, "fencing_token", 0)
    )
    if approve and fencing_token <= 0:
        raise HTTPException(
            status_code=409,
            detail="Aktif bakım lease'i gerekli",
        )

    try:
        result = service.decide_and_close(
            request_id=request_id,
            decided_by=principal.subject,
            approve=approve,
            decision_note=decision_note,
            fencing_token=fencing_token,
        )
    except ApprovalConflict as exc:
        raise HTTPException(
            status_code=409,
            detail=str(exc),
        ) from exc
    except ApprovalExpired as exc:
        raise HTTPException(
            status_code=410,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    metrics.increment(
        "aslan_quarantine_close_approved_total"
        if result.approval_status == "APPROVED"
        else "aslan_quarantine_close_rejected_total"
    )
    return result.__dict__

@app.get("/admin/session-maintenance-quarantine/{claim_id}/close-requests")
def list_verified_quarantine_close_requests(
    claim_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    repository = app.state.quarantine_approval_repository
    if repository is None:
        return {
            "enabled": False,
            "items": [],
            "chain_valid": False,
        }

    return {
        "enabled": True,
        "items": [
            item.__dict__
            for item in repository.list_claim(claim_id)
        ],
        "chain_valid": repository.verify_chain(claim_id),
    }

@app.get("/admin/session-maintenance-quarantine/{claim_id}/diagnose")
def diagnose_quarantined_index(
    claim_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    service = app.state.quarantine_diagnostics
    if service is None:
        raise HTTPException(status_code=409, detail="Karantina tanılama etkin değil")
    try:
        return service.inspect(claim_id).__dict__
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

@app.post("/admin/session-maintenance-quarantine/{claim_id}/retry")
def retry_quarantined_index(
    claim_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    service = app.state.quarantine_retry_service
    if service is None:
        raise HTTPException(status_code=409, detail="Karantina retry etkin değil")
    try:
        result = service.retry(claim_id=claim_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    metrics.increment(
        "aslan_session_maintenance_quarantine_retry_success_total"
        if result.status == "SUCCEEDED"
        else "aslan_session_maintenance_quarantine_retry_failure_total"
    )
    return result.__dict__

@app.post("/admin/session-maintenance-quarantine/{claim_id}/release")
def release_quarantined_index(
    claim_id: str,
    note: str = Query(min_length=3, max_length=1000),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.session_maintenance_worker
    manager = app.state.quarantine_manager
    if worker is None or manager is None:
        raise HTTPException(status_code=409, detail="Karantina yönetimi etkin değil")

    fencing_token = int(getattr(worker.lease, "fencing_token", 0))
    if fencing_token <= 0:
        raise HTTPException(status_code=409, detail="Aktif bakım lease'i gerekli")

    try:
        action = manager.release(
            claim_id=claim_id,
            operator=principal.subject,
            note=note,
            fencing_token=fencing_token,
        )
        progress = manager.requeue(
            action=action,
            progress_repository=worker.maintainer.progress_repository,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except StaleFencingToken as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    return {
        "action": action.__dict__,
        "progress": progress.__dict__,
    }

@app.get("/admin/session-maintenance-quarantine/{claim_id}/history")
def quarantine_history(
    claim_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    manager = app.state.quarantine_manager
    if manager is None:
        return {"enabled": False, "items": []}
    return {
        "enabled": True,
        "items": [item.__dict__ for item in manager.history(claim_id)],
    }

@app.get("/auth/session-maintenance-quarantine")
def session_maintenance_quarantine(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.session_maintenance_worker
    if (
        worker is None
        or worker.maintainer.journal is None
    ):
        return {
            "enabled": False,
            "items": [],
        }

    items = (
        worker
        .maintainer
        .journal
        .quarantined_indexes()
    )
    return {
        "enabled": True,
        "items": [
            item.__dict__
            for item in items
        ],
    }

@app.get("/auth/session-maintenance-journal")
def session_maintenance_journal(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.session_maintenance_worker
    if (
        worker is None
        or worker.maintainer.journal is None
    ):
        return {
            "enabled": False,
            "recoverable_claims": [],
        }

    claims = (
        worker
        .maintainer
        .journal
        .recoverable_claims()
    )
    return {
        "enabled": True,
        "recoverable_claims": [
            item.__dict__
            for item in claims
        ],
    }

@app.get("/auth/session-index-progress")
def session_index_progress(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.session_maintenance_worker
    if (
        worker is None
        or worker.maintainer.progress_repository is None
    ):
        return {
            "enabled": False,
            "progress": None,
        }

    progress = (
        worker
        .maintainer
        .progress_repository
        .load()
    )
    return {
        "enabled": True,
        "progress": progress.__dict__,
    }

@app.get("/auth/session-index-health")
def session_index_health(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.session_maintenance_worker
    report = (
        worker.last_report.__dict__
        if (
            worker is not None
            and worker.last_report is not None
        )
        else None
    )
    return {
        "enabled": worker is not None,
        "last_report": report,
        "last_error": (
            worker.last_error
            if worker is not None
            else None
        ),
        "lease": (
            worker.lease.state().__dict__
            if (
                worker is not None
                and worker.lease is not None
            )
            else None
        ),
    }

@app.post("/admin/session-index-maintenance/run")
async def run_session_index_maintenance(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    worker = app.state.session_maintenance_worker
    if worker is None:
        return {
            "enabled": False,
            "report": None,
        }

    report = await worker.run_once()
    return {
        "enabled": True,
        "report": report.__dict__,
    }

@app.get("/auth/cache-health")
def auth_cache_health(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin", "ops")
    ),
):
    discovery = (
        app.state.oidc_discovery_cache.health().__dict__
        if app.state.oidc_discovery_cache is not None
        else None
    )
    jwks = (
        app.state.oidc_jwks_cache.health().__dict__
        if app.state.oidc_jwks_cache is not None
        else None
    )
    return {
        "discovery": discovery,
        "jwks": jwks,
    }

@app.get("/auth/providers")
def auth_providers():
    return {
        "local": True,
        "oidc": app.state.oidc_verifier is not None,
        "oidc_issuer": (
            app.state.oidc_verifier.issuer
            if app.state.oidc_verifier is not None
            else None
        ),
        "oidc_discovery": (
            app.state.oidc_discovery_cache is not None
        ),
    }

@app.get("/auth/signing-keys")
def signing_keys():
    return {"keys": list(app.state.jwt_key_ring.public_metadata())}

@app.post("/admin/signing-keys/{key_id}/activate")
def activate_signing_key(
    key_id: str,
    secret: str = Query(min_length=16),
    principal: UnifiedPrincipal = Depends(require_app_roles("admin")),
):
    app.state.jwt_key_ring.add(
        key_id=key_id,
        secret=secret,
        activate=True,
    )
    return {
        "active_key_id": key_id,
        "keys": list(app.state.jwt_key_ring.public_metadata()),
    }


@app.get("/auth/sessions")
def list_sessions(
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "ops",
            "analyst",
            "viewer",
        )
    ),
):
    return [
        {
            "session_id": item.session_id,
            "family_id": item.family_id,
            "status": item.status,
            "rotation": item.rotation,
            "created_at": item.created_at,
            "last_used_at": item.last_used_at,
            "expires_at": item.expires_at,
            "user_agent": item.user_agent,
            "ip_address": item.ip_address,
        }
        for item in app.state.refresh_sessions.list_subject(
            principal.subject
        )
    ]

@app.post("/auth/sessions/{session_id}/revoke")
def revoke_session(
    session_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "ops",
            "analyst",
            "viewer",
        )
    ),
):
    session = app.state.refresh_sessions.get(
        session_id
    )
    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Refresh session bulunamadı",
        )
    if (
        session.subject != principal.subject
        and "admin" not in principal.roles
    ):
        raise HTTPException(
            status_code=403,
            detail="Bu oturum için yetkiniz yok",
        )

    revoked = app.state.refresh_sessions.revoke(
        session_id
    )
    return {
        "session_id": revoked.session_id,
        "status": revoked.status,
    }

@app.post("/auth/logout-all")
def logout_all(
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "ops",
            "analyst",
            "viewer",
        )
    ),
):
    revoked_count = (
        app.state.refresh_sessions.revoke_subject(
            principal.subject
        )
    )
    return {
        "subject": principal.subject,
        "revoked_sessions": revoked_count,
    }

@app.post("/auth/revoke")
def revoke_token(
    request: Request,
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "analyst", "viewer")),
):
    token = request.headers["Authorization"].removeprefix("Bearer ").strip()
    request.app.state.token_service.revoke(token)
    return {"revoked": True, "token_id": principal.token_id}

@app.post("/auth/ws-ticket")
def websocket_ticket(
    principal: UnifiedPrincipal = Depends(require_app_roles("admin", "ops", "analyst", "viewer")),
):
    ticket = app.state.ws_tickets.issue(
        subject=principal.subject,
        roles=principal.roles,
        ttl_seconds=30,
    )
    return {"ticket": ticket.ticket, "expires_at": ticket.expires_at}


@app.get("/admin/api-keys")
def list_api_keys(
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    return [
        {
            "key_id": item.key_id,
            "roles": list(item.roles),
            "status": item.status,
            "version": item.version,
        }
        for item in app.state.api_key_registry.list()
    ]

@app.post("/admin/api-keys/{key_id}/rotate")
def rotate_api_key(
    key_id: str,
    new_secret: str = Query(min_length=16),
    grace_seconds: int = Query(default=0, ge=0, le=3600),
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    try:
        item = app.state.api_key_registry.rotate(
            key_id=key_id,
            new_secret=new_secret,
            grace_seconds=grace_seconds,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "key_id": item.key_id,
        "status": item.status,
        "version": item.version,
    }

@app.post("/admin/api-keys/{key_id}/revoke")
def revoke_api_key(
    key_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles("admin")
    ),
):
    try:
        item = app.state.api_key_registry.revoke(key_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return {
        "key_id": item.key_id,
        "status": item.status,
        "version": item.version,
    }

@app.post(
    "/fixtures/{fixture_id}/provider-events",
    response_model=MatchStateOut,
)
async def append_provider_event(
    fixture_id: str,
    item: EventIn,
    api_key = Depends(provider_api_key),
):
    if item.fixture_id != fixture_id:
        raise HTTPException(status_code=400, detail="fixture_id uyuşmuyor")
    event = MatchEvent(**item.model_dump())
    event.validate()
    if not event_repository.append(event):
        raise HTTPException(status_code=409, detail="sequence zaten mevcut")
    state = service.rebuild(fixture_id, event_repository.list(fixture_id))
    payload = MatchStateOut(**state.__dict__).model_dump()
    await manager.broadcast(fixture_id, payload)
    return payload

@app.post(
    "/fixtures/{fixture_id}/events",
    response_model=MatchStateOut,
)
async def append_event(
    fixture_id: str,
    item: EventIn,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "provider",
            "ops",
        )
    ),
):
    metrics.increment(
        "aslan_api_event_requests_total"
    )
    correlation_id = (
        correlation_id_var.get()
    )

    if item.fixture_id != fixture_id:
        metrics.increment(
            "aslan_api_event_errors_total"
        )
        app.state.audit_repository.append(
            make_audit_event(
                action="fixture_event_append",
                subject=principal.subject,
                resource=fixture_id,
                outcome="rejected",
                correlation_id=correlation_id,
                metadata={
                    "reason": "fixture_id_mismatch"
                },
            )
        )
        raise HTTPException(
            status_code=400,
            detail="fixture_id uyuşmuyor",
        )

    event = MatchEvent(
        **item.model_dump()
    )
    event.validate()

    if not event_repository.append(event):
        metrics.increment(
            "aslan_api_event_duplicates_total"
        )
        app.state.audit_repository.append(
            make_audit_event(
                action="fixture_event_append",
                subject=principal.subject,
                resource=fixture_id,
                outcome="duplicate",
                correlation_id=correlation_id,
                metadata={
                    "sequence": event.sequence
                },
            )
        )
        raise HTTPException(
            status_code=409,
            detail="sequence zaten mevcut",
        )

    metrics.increment(
        "aslan_api_events_accepted_total"
    )
    app.state.audit_repository.append(
        make_audit_event(
            action="fixture_event_append",
            subject=principal.subject,
            resource=fixture_id,
            outcome="accepted",
            correlation_id=correlation_id,
            metadata={
                "sequence": event.sequence,
                "event_type": event.event_type,
            },
        )
    )

    state = service.rebuild(
        fixture_id,
        event_repository.list(
            fixture_id
        ),
    )
    payload = MatchStateOut(
        **state.__dict__
    ).model_dump()
    await manager.broadcast(
        fixture_id,
        payload,
    )
    return payload

@app.get(
    "/fixtures/{fixture_id}/state",
    response_model=MatchStateOut,
)
def fixture_state(
    fixture_id: str,
    principal: UnifiedPrincipal = Depends(
        require_app_roles(
            "admin",
            "ops",
            "analyst",
            "viewer",
        )
    ),
):
    return MatchStateOut(
        **service.rebuild(
            fixture_id,
            event_repository.list(
                fixture_id
            ),
        ).__dict__
    )

@app.websocket(
    "/ws/fixtures/{fixture_id}"
)
async def fixture_stream(
    websocket: WebSocket,
    fixture_id: str,
):
    ticket_value = websocket.query_params.get("ticket")
    ticket = (
        app.state.ws_tickets.consume(ticket_value)
        if ticket_value
        else None
    )
    if ticket is None:
        await websocket.close(code=4401)
        return
    if not set(("admin", "ops", "analyst", "viewer")).intersection(ticket.roles):
        await websocket.close(code=4403)
        return

    await manager.connect(
        fixture_id,
        websocket,
    )
    try:
        state = service.rebuild(
            fixture_id,
            event_repository.list(
                fixture_id
            ),
        )
        await websocket.send_json(
            MatchStateOut(
                **state.__dict__
            ).model_dump()
        )
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(
            fixture_id,
            websocket,
        )

@app.get("/fixtures")
def list_fixtures():
    with SessionLocal() as session:
        rows = session.execute(
            text(
                """
                SELECT
                    fixture_id,
                    provider,
                    provider_fixture_id,
                    league_name,
                    home_team,
                    away_team,
                    kickoff_at,
                    status
                FROM fixtures
                ORDER BY kickoff_at ASC
                LIMIT 100
                """
            )
        ).mappings().all()

    return {
        "count": len(rows),
        "fixtures": [dict(row) for row in rows],
    }
