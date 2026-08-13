from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import time


@dataclass(frozen=True)
class GovernancePolicy:
    policy_id: str
    tenant_id: str
    version: int
    name: str
    category: str
    scope: str
    status: str
    owner: str
    rules: tuple[str, ...]
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class GovernanceControl:
    control_id: str
    tenant_id: str
    name: str
    policy_ids: tuple[str, ...]
    required_evidence_types: tuple[str, ...]
    created_at: int


@dataclass(frozen=True)
class GovernanceEvidence:
    evidence_id: str
    tenant_id: str
    evidence_type: str
    source_system: str
    source_reference: str
    integrity_sha256: str
    metadata_json: str
    collected_at: int


@dataclass(frozen=True)
class PolicyEvaluation:
    evaluation_id: str
    tenant_id: str
    policy_id: str
    policy_version: int
    resource: str
    result: str
    violations: tuple[str, ...]
    evidence_ids: tuple[str, ...]
    evaluated_at: int


class GovernanceValidationError(ValueError):
    pass


class GovernanceError(RuntimeError):
    pass


class RedisGovernanceRepository:
    def __init__(self, client, *, prefix: str = "aslan:governance", ttl_seconds: int = 31536000):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save_policy(self, policy: GovernancePolicy) -> GovernancePolicy:
        payload = {**policy.__dict__, "rules": list(policy.rules)}
        self.client.setex(self._policy_key(policy.tenant_id, policy.policy_id, policy.version), self.ttl_seconds, json.dumps(payload, separators=(",", ":")))
        self.client.sadd(self._policy_index(policy.tenant_id), f"{policy.policy_id}:{policy.version}")
        return policy

    def list_policies(self, tenant_id: str) -> tuple[GovernancePolicy, ...]:
        items = []
        for token in self.client.smembers(self._policy_index(tenant_id)):
            if isinstance(token, bytes):
                token = token.decode()
            policy_id, version = str(token).rsplit(":", 1)
            payload = self.client.get(self._policy_key(tenant_id, policy_id, int(version)))
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode()
            data = json.loads(payload)
            data["rules"] = tuple(data["rules"])
            items.append(GovernancePolicy(**data))
        return tuple(sorted(items, key=lambda x: (x.policy_id, x.version)))

    def get_policy(self, *, tenant_id: str, policy_id: str, version: int | None = None) -> GovernancePolicy | None:
        items = [p for p in self.list_policies(tenant_id) if p.policy_id == policy_id]
        if not items:
            return None
        if version is None:
            return max(items, key=lambda x: x.version)
        return next((p for p in items if p.version == version), None)

    def save_control(self, control: GovernanceControl) -> GovernanceControl:
        payload = {**control.__dict__, "policy_ids": list(control.policy_ids), "required_evidence_types": list(control.required_evidence_types)}
        self.client.setex(self._control_key(control.tenant_id, control.control_id), self.ttl_seconds, json.dumps(payload, separators=(",", ":")))
        self.client.sadd(self._control_index(control.tenant_id), control.control_id)
        return control

    def list_controls(self, tenant_id: str) -> tuple[GovernanceControl, ...]:
        items = []
        for control_id in self.client.smembers(self._control_index(tenant_id)):
            if isinstance(control_id, bytes):
                control_id = control_id.decode()
            payload = self.client.get(self._control_key(tenant_id, str(control_id)))
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode()
            data = json.loads(payload)
            data["policy_ids"] = tuple(data["policy_ids"])
            data["required_evidence_types"] = tuple(data["required_evidence_types"])
            items.append(GovernanceControl(**data))
        return tuple(sorted(items, key=lambda x: x.control_id))

    def save_evidence(self, evidence: GovernanceEvidence) -> GovernanceEvidence:
        self.client.setex(self._evidence_key(evidence.tenant_id, evidence.evidence_id), self.ttl_seconds, json.dumps(evidence.__dict__, separators=(",", ":")))
        self.client.sadd(self._evidence_index(evidence.tenant_id), evidence.evidence_id)
        return evidence

    def list_evidence(self, tenant_id: str) -> tuple[GovernanceEvidence, ...]:
        items = []
        for evidence_id in self.client.smembers(self._evidence_index(tenant_id)):
            if isinstance(evidence_id, bytes):
                evidence_id = evidence_id.decode()
            payload = self.client.get(self._evidence_key(tenant_id, str(evidence_id)))
            if payload is None:
                continue
            if isinstance(payload, bytes):
                payload = payload.decode()
            items.append(GovernanceEvidence(**json.loads(payload)))
        return tuple(sorted(items, key=lambda x: x.collected_at))

    def save_evaluation(self, evaluation: PolicyEvaluation) -> PolicyEvaluation:
        payload = {**evaluation.__dict__, "violations": list(evaluation.violations), "evidence_ids": list(evaluation.evidence_ids)}
        self.client.setex(f"{self.prefix}:evaluation:{evaluation.tenant_id}:{evaluation.evaluation_id}", self.ttl_seconds, json.dumps(payload, separators=(",", ":")))
        return evaluation

    def _policy_key(self, tenant_id: str, policy_id: str, version: int) -> str:
        return f"{self.prefix}:policy:{tenant_id}:{policy_id}:{version}"

    def _policy_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:policies:{tenant_id}"

    def _control_key(self, tenant_id: str, control_id: str) -> str:
        return f"{self.prefix}:control:{tenant_id}:{control_id}"

    def _control_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:controls:{tenant_id}"

    def _evidence_key(self, tenant_id: str, evidence_id: str) -> str:
        return f"{self.prefix}:evidence:{tenant_id}:{evidence_id}"

    def _evidence_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:evidence-index:{tenant_id}"


class GovernanceService:
    VALID_CATEGORIES = {"SECURITY", "DEPLOYMENT", "RELIABILITY", "AI", "DATA", "COMPLIANCE", "OPERATIONS"}

    def __init__(self, *, repository):
        self.repository = repository

    def create_policy(self, *, policy_id: str, tenant_id: str, name: str, category: str, scope: str, owner: str, rules: tuple[str, ...], now: int | None = None) -> GovernancePolicy:
        category = category.upper()
        if category not in self.VALID_CATEGORIES:
            raise GovernanceValidationError("Geçersiz policy category")
        if not rules:
            raise GovernanceValidationError("En az bir policy rule gereklidir")
        current = int(now if now is not None else time.time())
        return self.repository.save_policy(GovernancePolicy(policy_id, tenant_id, 1, name, category, scope, "DRAFT", owner, rules, current, current))

    def version_policy(self, *, tenant_id: str, policy_id: str, rules: tuple[str, ...], owner: str, now: int | None = None) -> GovernancePolicy:
        current = self.repository.get_policy(tenant_id=tenant_id, policy_id=policy_id)
        if current is None:
            raise KeyError("Policy bulunamadı")
        return self.repository.save_policy(GovernancePolicy(current.policy_id, current.tenant_id, current.version + 1, current.name, current.category, current.scope, "DRAFT", owner, rules, current.created_at, int(now if now is not None else time.time())))

    def transition_policy(self, *, tenant_id: str, policy_id: str, version: int, target_status: str, now: int | None = None) -> GovernancePolicy:
        policy = self.repository.get_policy(tenant_id=tenant_id, policy_id=policy_id, version=version)
        if policy is None:
            raise KeyError("Policy bulunamadı")
        transitions = {"DRAFT": {"REVIEW"}, "REVIEW": {"APPROVED"}, "APPROVED": {"ACTIVE"}, "ACTIVE": {"DEPRECATED"}, "DEPRECATED": {"ARCHIVED"}, "ARCHIVED": set()}
        target = target_status.upper()
        if target not in transitions[policy.status]:
            raise GovernanceError(f"Geçersiz policy geçişi: {policy.status} -> {target}")
        updated = GovernancePolicy(**{**policy.__dict__, "status": target, "updated_at": int(now if now is not None else time.time())})
        return self.repository.save_policy(updated)

    def create_control(self, *, control_id: str, tenant_id: str, name: str, policy_ids: tuple[str, ...], required_evidence_types: tuple[str, ...], now: int | None = None) -> GovernanceControl:
        if not policy_ids:
            raise GovernanceValidationError("Control en az bir policy ile eşleşmelidir")
        return self.repository.save_control(GovernanceControl(control_id, tenant_id, name, policy_ids, tuple(x.upper() for x in required_evidence_types), int(now if now is not None else time.time())))

    def collect_evidence(self, *, evidence_id: str, tenant_id: str, evidence_type: str, source_system: str, source_reference: str, metadata: dict, now: int | None = None) -> GovernanceEvidence:
        metadata_json = json.dumps(metadata, sort_keys=True, separators=(",", ":"))
        digest = hashlib.sha256(f"{evidence_id}|{tenant_id}|{evidence_type.upper()}|{source_system}|{source_reference}|{metadata_json}".encode()).hexdigest()
        return self.repository.save_evidence(GovernanceEvidence(evidence_id, tenant_id, evidence_type.upper(), source_system, source_reference, digest, metadata_json, int(now if now is not None else time.time())))

    def evaluate_policy(self, *, evaluation_id: str, tenant_id: str, policy_id: str, resource: str, facts: dict, evidence_ids: tuple[str, ...], now: int | None = None) -> PolicyEvaluation:
        policy = self.repository.get_policy(tenant_id=tenant_id, policy_id=policy_id)
        if policy is None:
            raise KeyError("Policy bulunamadı")
        if policy.status != "ACTIVE":
            raise GovernanceError("Yalnızca ACTIVE policy değerlendirilebilir")
        violations = []
        for rule in policy.rules:
            if "=" not in rule:
                violations.append(f"Geçersiz rule formatı: {rule}")
                continue
            key, expected = [x.strip() for x in rule.split("=", 1)]
            actual = facts.get(key)
            if str(actual).lower() != expected.lower():
                violations.append(f"{key} beklenen={expected} gerçek={actual}")
        result = "COMPLIANT" if not violations else "NON_COMPLIANT"
        return self.repository.save_evaluation(PolicyEvaluation(evaluation_id, tenant_id, policy.policy_id, policy.version, resource, result, tuple(violations), evidence_ids, int(now if now is not None else time.time())))

    def compliance_report(self, *, tenant_id: str, now: int | None = None) -> dict:
        controls = self.repository.list_controls(tenant_id)
        active_policy_ids = {p.policy_id for p in self.repository.list_policies(tenant_id) if p.status == "ACTIVE"}
        evidence_types = {e.evidence_type for e in self.repository.list_evidence(tenant_id)}
        compliant = 0
        gaps = []
        for control in controls:
            missing_policies = [p for p in control.policy_ids if p not in active_policy_ids]
            missing_evidence = [e for e in control.required_evidence_types if e not in evidence_types]
            if not missing_policies and not missing_evidence:
                compliant += 1
            else:
                if missing_policies:
                    gaps.append(f"{control.control_id}: policy eksik={','.join(missing_policies)}")
                if missing_evidence:
                    gaps.append(f"{control.control_id}: evidence eksik={','.join(missing_evidence)}")
        total = len(controls)
        return {
            "tenant_id": tenant_id,
            "total_controls": total,
            "compliant_controls": compliant,
            "non_compliant_controls": total - compliant,
            "audit_readiness": "READY" if total == compliant else "PARTIAL" if compliant else "NOT_READY",
            "gaps": gaps,
            "generated_at": int(now if now is not None else time.time()),
        }
