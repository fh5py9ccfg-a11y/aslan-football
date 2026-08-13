from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time


@dataclass(frozen=True)
class FeatureFlag:
    flag_id: str
    club_id: str
    name: str
    enabled: bool
    rollout_percentage: int
    allowed_roles: tuple[str, ...]
    variant: str
    updated_at: int


@dataclass(frozen=True)
class Experiment:
    experiment_id: str
    club_id: str
    name: str
    feature: str
    control_variant: str
    treatment_variant: str
    rollout_percentage: int
    status: str
    primary_metric: str
    started_at: int
    ended_at: int


@dataclass(frozen=True)
class ExperimentAssignment:
    assignment_id: str
    experiment_id: str
    club_id: str
    user_id: str
    variant: str
    assigned_at: int


@dataclass(frozen=True)
class ExperimentMetric:
    metric_id: str
    experiment_id: str
    club_id: str
    user_id: str
    variant: str
    metric_name: str
    metric_value: float
    success: bool
    recorded_at: int


@dataclass(frozen=True)
class ExperimentReport:
    report_id: str
    experiment_id: str
    control_users: int
    treatment_users: int
    control_mean: float
    treatment_mean: float
    uplift_percentage: float
    control_success_rate: float
    treatment_success_rate: float
    winner: str
    recommendation: str
    generated_at: int


class ExperimentValidationError(ValueError):
    pass


class RedisPilotExperimentRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:pilot-experiments",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_flag(self, item: FeatureFlag) -> FeatureFlag:
        payload = {
            **item.__dict__,
            "allowed_roles": list(item.allowed_roles),
        }
        self.client.setex(
            self._flag_key(item.flag_id),
            self.ttl_seconds,
            json.dumps(payload, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_flag_index(item.club_id),
            item.flag_id,
        )
        return item

    def get_flag(self, flag_id: str) -> FeatureFlag | None:
        payload = self.client.get(self._flag_key(flag_id))
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        data = json.loads(payload)
        data["allowed_roles"] = tuple(data["allowed_roles"])
        return FeatureFlag(**data)

    def list_flags(self, club_id: str) -> tuple[FeatureFlag, ...]:
        items = []
        for flag_id in self.client.smembers(
            self._club_flag_index(club_id)
        ):
            if isinstance(flag_id, bytes):
                flag_id = flag_id.decode("utf-8")
            item = self.get_flag(str(flag_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.name.lower())
        return tuple(items)

    def save_experiment(self, item: Experiment) -> Experiment:
        self.client.setex(
            self._experiment_key(item.experiment_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._club_experiment_index(item.club_id),
            item.experiment_id,
        )
        return item

    def get_experiment(self, experiment_id: str) -> Experiment | None:
        payload = self.client.get(
            self._experiment_key(experiment_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return Experiment(**json.loads(payload))

    def list_experiments(
        self,
        club_id: str,
    ) -> tuple[Experiment, ...]:
        items = []
        for experiment_id in self.client.smembers(
            self._club_experiment_index(club_id)
        ):
            if isinstance(experiment_id, bytes):
                experiment_id = experiment_id.decode("utf-8")
            item = self.get_experiment(str(experiment_id))
            if item is not None:
                items.append(item)
        items.sort(key=lambda item: item.started_at, reverse=True)
        return tuple(items)

    def save_assignment(
        self,
        item: ExperimentAssignment,
    ) -> ExperimentAssignment:
        self.client.setex(
            self._assignment_key(item.assignment_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._experiment_assignment_index(
                item.experiment_id
            ),
            item.assignment_id,
        )
        return item

    def list_assignments(
        self,
        experiment_id: str,
    ) -> tuple[ExperimentAssignment, ...]:
        items = []
        for assignment_id in self.client.smembers(
            self._experiment_assignment_index(
                experiment_id
            )
        ):
            if isinstance(assignment_id, bytes):
                assignment_id = assignment_id.decode("utf-8")
            payload = self.client.get(
                self._assignment_key(str(assignment_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                ExperimentAssignment(**json.loads(payload))
            )
        items.sort(key=lambda item: item.assigned_at)
        return tuple(items)

    def save_metric(self, item: ExperimentMetric) -> ExperimentMetric:
        self.client.setex(
            self._metric_key(item.metric_id),
            self.ttl_seconds,
            json.dumps(item.__dict__, ensure_ascii=False),
        )
        self.client.sadd(
            self._experiment_metric_index(
                item.experiment_id
            ),
            item.metric_id,
        )
        return item

    def list_metrics(
        self,
        experiment_id: str,
    ) -> tuple[ExperimentMetric, ...]:
        items = []
        for metric_id in self.client.smembers(
            self._experiment_metric_index(
                experiment_id
            )
        ):
            if isinstance(metric_id, bytes):
                metric_id = metric_id.decode("utf-8")
            payload = self.client.get(
                self._metric_key(str(metric_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                ExperimentMetric(**json.loads(payload))
            )
        items.sort(key=lambda item: item.recorded_at)
        return tuple(items)

    def _flag_key(self, flag_id: str) -> str:
        return f"{self.prefix}:flag:{flag_id}"

    def _club_flag_index(self, club_id: str) -> str:
        return f"{self.prefix}:flags:{club_id}"

    def _experiment_key(self, experiment_id: str) -> str:
        return f"{self.prefix}:experiment:{experiment_id}"

    def _club_experiment_index(self, club_id: str) -> str:
        return f"{self.prefix}:experiments:{club_id}"

    def _assignment_key(self, assignment_id: str) -> str:
        return f"{self.prefix}:assignment:{assignment_id}"

    def _experiment_assignment_index(
        self,
        experiment_id: str,
    ) -> str:
        return f"{self.prefix}:assignments:{experiment_id}"

    def _metric_key(self, metric_id: str) -> str:
        return f"{self.prefix}:metric:{metric_id}"

    def _experiment_metric_index(
        self,
        experiment_id: str,
    ) -> str:
        return f"{self.prefix}:metrics:{experiment_id}"


class PilotExperimentService:
    EXPERIMENT_STATUSES = {
        "DRAFT",
        "RUNNING",
        "PAUSED",
        "COMPLETED",
        "ROLLED_BACK",
    }

    def __init__(self, *, repository):
        self.repository = repository

    def create_flag(
        self,
        *,
        flag_id: str,
        club_id: str,
        name: str,
        enabled: bool,
        rollout_percentage: int,
        allowed_roles: tuple[str, ...] = (),
        variant: str = "default",
        now: int | None = None,
    ) -> FeatureFlag:
        if not 0 <= rollout_percentage <= 100:
            raise ExperimentValidationError(
                "Rollout yüzdesi 0 ile 100 arasında olmalıdır"
            )
        item = FeatureFlag(
            flag_id=flag_id,
            club_id=club_id,
            name=name.strip(),
            enabled=enabled,
            rollout_percentage=rollout_percentage,
            allowed_roles=tuple(
                role.strip().upper()
                for role in allowed_roles
                if role.strip()
            ),
            variant=variant.strip(),
            updated_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_flag(item)

    def evaluate_flag(
        self,
        *,
        flag_id: str,
        user_id: str,
        role: str,
    ) -> dict:
        flag = self.repository.get_flag(flag_id)
        if flag is None:
            raise KeyError("Feature flag bulunamadı")
        role_allowed = (
            not flag.allowed_roles
            or role.upper() in flag.allowed_roles
        )
        bucket = int(
            hashlib.sha256(
                f"{flag_id}:{user_id}".encode("utf-8")
            ).hexdigest()[:8],
            16,
        ) % 100
        enabled = (
            flag.enabled
            and role_allowed
            and bucket < flag.rollout_percentage
        )
        return {
            "flag_id": flag_id,
            "enabled": enabled,
            "variant": flag.variant if enabled else "control",
            "bucket": bucket,
            "rollout_percentage": flag.rollout_percentage,
            "role_allowed": role_allowed,
        }

    def create_experiment(
        self,
        *,
        experiment_id: str,
        club_id: str,
        name: str,
        feature: str,
        control_variant: str,
        treatment_variant: str,
        rollout_percentage: int,
        primary_metric: str,
        status: str = "DRAFT",
        now: int | None = None,
    ) -> Experiment:
        normalized = status.upper()
        if normalized not in self.EXPERIMENT_STATUSES:
            raise ExperimentValidationError(
                "Geçersiz deney durumu"
            )
        if not 1 <= rollout_percentage <= 100:
            raise ExperimentValidationError(
                "Deney rollout yüzdesi 1 ile 100 arasında olmalıdır"
            )
        current = int(now if now is not None else time.time())
        item = Experiment(
            experiment_id=experiment_id,
            club_id=club_id,
            name=name.strip(),
            feature=feature.strip().upper(),
            control_variant=control_variant.strip(),
            treatment_variant=treatment_variant.strip(),
            rollout_percentage=rollout_percentage,
            status=normalized,
            primary_metric=primary_metric.strip(),
            started_at=current if normalized == "RUNNING" else 0,
            ended_at=0,
        )
        return self.repository.save_experiment(item)

    def update_experiment_status(
        self,
        *,
        experiment_id: str,
        status: str,
        now: int | None = None,
    ) -> Experiment:
        experiment = self.repository.get_experiment(
            experiment_id
        )
        if experiment is None:
            raise KeyError("Deney bulunamadı")
        normalized = status.upper()
        if normalized not in self.EXPERIMENT_STATUSES:
            raise ExperimentValidationError(
                "Geçersiz deney durumu"
            )
        current = int(now if now is not None else time.time())
        updated = Experiment(
            **{
                **experiment.__dict__,
                "status": normalized,
                "started_at": (
                    experiment.started_at
                    or (
                        current
                        if normalized == "RUNNING"
                        else 0
                    )
                ),
                "ended_at": (
                    current
                    if normalized
                    in {"COMPLETED", "ROLLED_BACK"}
                    else experiment.ended_at
                ),
            }
        )
        return self.repository.save_experiment(updated)

    def assign_variant(
        self,
        *,
        assignment_id: str,
        experiment_id: str,
        club_id: str,
        user_id: str,
        now: int | None = None,
    ) -> ExperimentAssignment:
        experiment = self.repository.get_experiment(
            experiment_id
        )
        if experiment is None:
            raise KeyError("Deney bulunamadı")
        if experiment.status != "RUNNING":
            raise ExperimentValidationError(
                "Deney RUNNING durumunda değil"
            )
        bucket = int(
            hashlib.sha256(
                f"{experiment_id}:{user_id}".encode("utf-8")
            ).hexdigest()[:8],
            16,
        ) % 100
        if bucket >= experiment.rollout_percentage:
            variant = experiment.control_variant
        else:
            variant = (
                experiment.treatment_variant
                if bucket % 2
                else experiment.control_variant
            )
        item = ExperimentAssignment(
            assignment_id=assignment_id,
            experiment_id=experiment_id,
            club_id=club_id,
            user_id=user_id,
            variant=variant,
            assigned_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_assignment(item)

    def record_metric(
        self,
        *,
        metric_id: str,
        experiment_id: str,
        club_id: str,
        user_id: str,
        variant: str,
        metric_name: str,
        metric_value: float,
        success: bool,
        now: int | None = None,
    ) -> ExperimentMetric:
        experiment = self.repository.get_experiment(
            experiment_id
        )
        if experiment is None:
            raise KeyError("Deney bulunamadı")
        allowed_variants = {
            experiment.control_variant,
            experiment.treatment_variant,
        }
        if variant not in allowed_variants:
            raise ExperimentValidationError(
                "Geçersiz deney varyantı"
            )
        item = ExperimentMetric(
            metric_id=metric_id,
            experiment_id=experiment_id,
            club_id=club_id,
            user_id=user_id,
            variant=variant,
            metric_name=metric_name,
            metric_value=metric_value,
            success=success,
            recorded_at=int(now if now is not None else time.time()),
        )
        return self.repository.save_metric(item)

    def report(
        self,
        *,
        report_id: str,
        experiment_id: str,
        now: int | None = None,
    ) -> ExperimentReport:
        experiment = self.repository.get_experiment(
            experiment_id
        )
        if experiment is None:
            raise KeyError("Deney bulunamadı")
        metrics = self.repository.list_metrics(
            experiment_id
        )
        control = [
            item for item in metrics
            if item.variant == experiment.control_variant
        ]
        treatment = [
            item for item in metrics
            if item.variant == experiment.treatment_variant
        ]
        control_mean = (
            sum(item.metric_value for item in control)
            / len(control)
            if control
            else 0.0
        )
        treatment_mean = (
            sum(item.metric_value for item in treatment)
            / len(treatment)
            if treatment
            else 0.0
        )
        uplift = (
            (treatment_mean - control_mean)
            / abs(control_mean)
            * 100
            if control_mean != 0
            else 0.0
        )
        control_success = (
            sum(1 for item in control if item.success)
            / len(control) * 100
            if control
            else 0.0
        )
        treatment_success = (
            sum(1 for item in treatment if item.success)
            / len(treatment) * 100
            if treatment
            else 0.0
        )

        if len(control) < 5 or len(treatment) < 5:
            winner = "INCONCLUSIVE"
            recommendation = "Daha fazla örneklem topla"
        elif (
            treatment_mean > control_mean
            and treatment_success >= control_success
        ):
            winner = experiment.treatment_variant
            recommendation = "Tedavi varyantını kademeli genişlet"
        elif (
            treatment_mean < control_mean
            or treatment_success + 5 < control_success
        ):
            winner = experiment.control_variant
            recommendation = "Tedavi varyantını geri al"
        else:
            winner = "INCONCLUSIVE"
            recommendation = "Deneyi sürdür ve ek metrik incele"

        return ExperimentReport(
            report_id=report_id,
            experiment_id=experiment_id,
            control_users=len({
                item.user_id for item in control
            }),
            treatment_users=len({
                item.user_id for item in treatment
            }),
            control_mean=round(control_mean, 4),
            treatment_mean=round(treatment_mean, 4),
            uplift_percentage=round(uplift, 2),
            control_success_rate=round(control_success, 2),
            treatment_success_rate=round(
                treatment_success,
                2,
            ),
            winner=winner,
            recommendation=recommendation,
            generated_at=int(now if now is not None else time.time()),
        )

    def rollback_experiment(
        self,
        *,
        experiment_id: str,
        flag_id: str | None = None,
        now: int | None = None,
    ) -> dict:
        experiment = self.update_experiment_status(
            experiment_id=experiment_id,
            status="ROLLED_BACK",
            now=now,
        )
        flag = None
        if flag_id is not None:
            current = self.repository.get_flag(flag_id)
            if current is None:
                raise KeyError("Feature flag bulunamadı")
            flag = self.create_flag(
                flag_id=current.flag_id,
                club_id=current.club_id,
                name=current.name,
                enabled=False,
                rollout_percentage=0,
                allowed_roles=current.allowed_roles,
                variant=current.variant,
                now=now,
            )
        return {
            "experiment": experiment.__dict__,
            "flag": (
                {
                    **flag.__dict__,
                    "allowed_roles": list(flag.allowed_roles),
                }
                if flag is not None
                else None
            ),
        }
