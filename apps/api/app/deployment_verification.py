from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class VerificationCheck:
    check_id: str
    session_id: str
    check_type: str
    name: str
    passed: bool
    value: float | None
    threshold: float | None
    detail: str
    observed_at: int


@dataclass(frozen=True)
class VerificationSession:
    session_id: str
    plan_id: str
    release_id: str
    deployment_slot: str
    status: str
    required_checks: int
    passed_checks: int
    failed_checks: int
    rollback_executed: bool
    rollback_generation: int | None
    rollback_model_id: str | None
    failure_reason: str | None
    created_at: int
    updated_at: int


class DeploymentVerificationError(RuntimeError):
    pass


class RedisDeploymentVerificationRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:deployment-verification",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_session(
        self,
        session: VerificationSession,
    ) -> VerificationSession:
        self.client.setex(
            self._session_key(session.session_id),
            self.ttl_seconds,
            json.dumps(
                session.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._plan_session_index(session.plan_id),
            session.session_id,
        )
        return session

    def get_session(
        self,
        session_id: str,
    ) -> VerificationSession | None:
        payload = self.client.get(
            self._session_key(session_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return VerificationSession(**json.loads(payload))

    def save_check(
        self,
        check: VerificationCheck,
    ) -> VerificationCheck:
        self.client.setex(
            self._check_key(check.check_id),
            self.ttl_seconds,
            json.dumps(
                check.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._session_check_index(check.session_id),
            check.check_id,
        )
        return check

    def list_checks(
        self,
        session_id: str,
    ) -> tuple[VerificationCheck, ...]:
        items = []
        for check_id in self.client.smembers(
            self._session_check_index(session_id)
        ):
            if isinstance(check_id, bytes):
                check_id = check_id.decode("utf-8")
            payload = self.client.get(
                self._check_key(str(check_id))
            )
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode("utf-8")
            items.append(
                VerificationCheck(**json.loads(payload))
            )
        items.sort(
            key=lambda item: (
                item.observed_at,
                item.check_id,
            )
        )
        return tuple(items)

    def list_sessions(
        self,
        plan_id: str,
        *,
        limit: int = 100,
    ) -> tuple[VerificationSession, ...]:
        items = []
        for session_id in self.client.smembers(
            self._plan_session_index(plan_id)
        ):
            if isinstance(session_id, bytes):
                session_id = session_id.decode("utf-8")
            session = self.get_session(str(session_id))
            if session is not None:
                items.append(session)
        items.sort(
            key=lambda item: item.created_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def _session_key(self, session_id: str) -> str:
        return f"{self.prefix}:session:{session_id}"

    def _plan_session_index(self, plan_id: str) -> str:
        return f"{self.prefix}:sessions:{plan_id}"

    def _check_key(self, check_id: str) -> str:
        return f"{self.prefix}:check:{check_id}"

    def _session_check_index(
        self,
        session_id: str,
    ) -> str:
        return f"{self.prefix}:checks:{session_id}"


class DeploymentVerificationService:
    def __init__(
        self,
        *,
        repository,
        progressive_delivery_service,
        deployment_manager,
    ):
        self.repository = repository
        self.progressive_delivery_service = (
            progressive_delivery_service
        )
        self.deployment_manager = deployment_manager

    def create_session(
        self,
        *,
        session_id: str,
        plan_id: str,
        deployment_slot: str,
        required_checks: int = 1,
        now: int | None = None,
    ) -> VerificationSession:
        if required_checks < 1:
            raise ValueError(
                "required_checks en az 1 olmalıdır"
            )

        plan = (
            self.progressive_delivery_service
            .repository.get_plan(plan_id)
        )
        if plan is None:
            raise KeyError(
                "Progressive delivery plan bulunamadı"
            )
        state = (
            self.progressive_delivery_service
            .repository.get_state(plan_id)
        )
        if state is None:
            raise KeyError(
                "Progressive delivery state bulunamadı"
            )
        if state.status not in {
            "RUNNING",
            "COMPLETED",
            "ROLLED_BACK",
            "PAUSED",
        }:
            raise DeploymentVerificationError(
                "Rollout doğrulama için uygun durumda değil"
            )

        current = int(
            now if now is not None
            else time.time()
        )
        session = VerificationSession(
            session_id=session_id,
            plan_id=plan_id,
            release_id=plan.release_id,
            deployment_slot=deployment_slot,
            status="OPEN",
            required_checks=required_checks,
            passed_checks=0,
            failed_checks=0,
            rollback_executed=False,
            rollback_generation=None,
            rollback_model_id=None,
            failure_reason=None,
            created_at=current,
            updated_at=current,
        )
        return self.repository.save_session(session)

    def record_check(
        self,
        *,
        session_id: str,
        check_id: str,
        check_type: str,
        name: str,
        passed: bool,
        detail: str,
        value: float | None = None,
        threshold: float | None = None,
        observed_at: int | None = None,
    ) -> tuple[
        VerificationSession,
        VerificationCheck,
    ]:
        session = self._required_session(session_id)
        if session.status not in {"OPEN", "VERIFYING"}:
            raise DeploymentVerificationError(
                "Verification session yeni check kabul etmiyor"
            )
        if self.repository.list_checks(session_id):
            if any(
                item.check_id == check_id
                for item in self.repository.list_checks(
                    session_id
                )
            ):
                raise DeploymentVerificationError(
                    "Verification check daha önce kaydedildi"
                )

        current = int(
            observed_at
            if observed_at is not None
            else time.time()
        )
        check = VerificationCheck(
            check_id=check_id,
            session_id=session_id,
            check_type=check_type.upper(),
            name=name,
            passed=passed,
            value=value,
            threshold=threshold,
            detail=detail,
            observed_at=current,
        )
        self.repository.save_check(check)

        passed_count = (
            session.passed_checks + (1 if passed else 0)
        )
        failed_count = (
            session.failed_checks + (0 if passed else 1)
        )
        status = (
            "FAILED"
            if failed_count > 0
            else "VERIFIED"
            if passed_count >= session.required_checks
            else "VERIFYING"
        )
        failure_reason = (
            detail
            if not passed
            else session.failure_reason
        )
        updated = VerificationSession(
            **{
                **session.__dict__,
                "status": status,
                "passed_checks": passed_count,
                "failed_checks": failed_count,
                "failure_reason": failure_reason,
                "updated_at": current,
            }
        )
        self.repository.save_session(updated)
        return updated, check

    def finalize(
        self,
        *,
        session_id: str,
        now: int | None = None,
    ) -> VerificationSession:
        session = self._required_session(session_id)
        if session.failed_checks > 0:
            raise DeploymentVerificationError(
                "Başarısız check bulunan session doğrulanamaz"
            )
        if session.passed_checks < session.required_checks:
            raise DeploymentVerificationError(
                "Zorunlu verification check sayısı tamamlanmadı"
            )

        state = (
            self.progressive_delivery_service
            .repository.get_state(session.plan_id)
        )
        if state is None:
            raise KeyError(
                "Progressive delivery state bulunamadı"
            )
        if state.status != "COMPLETED":
            raise DeploymentVerificationError(
                "Rollout tamamlanmadan verification finalize edilemez"
            )

        current = int(
            now if now is not None
            else time.time()
        )
        updated = VerificationSession(
            **{
                **session.__dict__,
                "status": "VERIFIED",
                "updated_at": current,
            }
        )
        return self.repository.save_session(updated)

    def execute_rollback(
        self,
        *,
        session_id: str,
        reason: str | None = None,
        now: int | None = None,
    ) -> VerificationSession:
        session = self._required_session(session_id)
        if session.rollback_executed:
            return session

        rollout_state = (
            self.progressive_delivery_service
            .repository.get_state(session.plan_id)
        )
        if rollout_state is None:
            raise KeyError(
                "Progressive delivery state bulunamadı"
            )
        if (
            session.failed_checks == 0
            and rollout_state.status != "ROLLED_BACK"
        ):
            raise DeploymentVerificationError(
                "Rollback için başarısız verification veya rollout rollback kararı gereklidir"
            )

        deployment = self.deployment_manager.rollback(
            slot=session.deployment_slot,
            now=now,
        )
        current = int(
            now if now is not None
            else time.time()
        )
        updated = VerificationSession(
            **{
                **session.__dict__,
                "status": "ROLLED_BACK",
                "rollback_executed": True,
                "rollback_generation": (
                    deployment.generation
                ),
                "rollback_model_id": (
                    deployment.champion_model_id
                ),
                "failure_reason": (
                    reason
                    or session.failure_reason
                    or rollout_state.rollback_reason
                    or "Deployment verification rollback"
                ),
                "updated_at": current,
            }
        )
        return self.repository.save_session(updated)

    def _required_session(
        self,
        session_id: str,
    ) -> VerificationSession:
        session = self.repository.get_session(
            session_id
        )
        if session is None:
            raise KeyError(
                "Verification session bulunamadı"
            )
        return session
