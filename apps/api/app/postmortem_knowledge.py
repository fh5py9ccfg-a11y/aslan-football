from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import re
import time


@dataclass(frozen=True)
class PostmortemEvidence:
    evidence_id: str
    kind: str
    summary: str
    reference: str | None
    recorded_at: int


@dataclass(frozen=True)
class PostmortemAction:
    action_id: str
    title: str
    owner: str
    due_at: int | None
    status: str
    completed_at: int | None


@dataclass(frozen=True)
class IncidentPostmortem:
    postmortem_id: str
    incident_id: str
    tenant_id: str
    title: str
    summary: str
    root_cause: str
    impact: str
    lessons: str
    contributing_factors: tuple[str, ...]
    evidence: tuple[PostmortemEvidence, ...]
    actions: tuple[PostmortemAction, ...]
    status: str
    revision: int
    created_at: int
    updated_at: int
    published_at: int | None


class PostmortemConflict(RuntimeError):
    pass


class PostmortemValidationError(RuntimeError):
    pass


class RedisPostmortemRepository:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:postmortem",
        ttl_seconds: int = 31_536_000,
    ):
        self.client = client
        self.prefix = prefix
        self.ttl_seconds = ttl_seconds

    def save(
        self,
        item: IncidentPostmortem,
        *,
        expected_revision: int | None = None,
    ) -> IncidentPostmortem:
        current = self.get(item.postmortem_id)
        if (
            expected_revision is not None
            and (
                current is None
                or current.revision != expected_revision
            )
        ):
            raise PostmortemConflict(
                "Postmortem revision çakışması"
            )

        payload = self._serialize(item)
        self.client.setex(
            self._item_key(item.postmortem_id),
            self.ttl_seconds,
            payload,
        )
        self.client.sadd(
            self._tenant_index(item.tenant_id),
            item.postmortem_id,
        )
        self.client.setex(
            self._incident_key(item.incident_id),
            self.ttl_seconds,
            item.postmortem_id,
        )
        return item

    def get(
        self,
        postmortem_id: str,
    ) -> IncidentPostmortem | None:
        payload = self.client.get(
            self._item_key(postmortem_id)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return self._deserialize(payload)

    def get_by_incident(
        self,
        incident_id: str,
    ) -> IncidentPostmortem | None:
        postmortem_id = self.client.get(
            self._incident_key(incident_id)
        )
        if postmortem_id is None:
            return None
        if isinstance(postmortem_id, bytes):
            postmortem_id = postmortem_id.decode("utf-8")
        return self.get(str(postmortem_id))

    def list_tenant(
        self,
        tenant_id: str,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> tuple[IncidentPostmortem, ...]:
        items = []
        for postmortem_id in self.client.smembers(
            self._tenant_index(tenant_id)
        ):
            if isinstance(postmortem_id, bytes):
                postmortem_id = postmortem_id.decode("utf-8")
            item = self.get(str(postmortem_id))
            if item is None:
                continue
            if status is not None and item.status != status:
                continue
            items.append(item)
        items.sort(
            key=lambda item: item.updated_at,
            reverse=True,
        )
        return tuple(items[:limit])

    def search_similar(
        self,
        *,
        tenant_id: str,
        query: str,
        limit: int = 5,
    ) -> tuple[tuple[IncidentPostmortem, float], ...]:
        query_tokens = _tokens(query)
        if not query_tokens:
            return ()

        matches = []
        for item in self.list_tenant(
            tenant_id,
            status="PUBLISHED",
            limit=1000,
        ):
            document = " ".join(
                (
                    item.title,
                    item.summary,
                    item.root_cause,
                    item.impact,
                    item.lessons,
                    " ".join(item.contributing_factors),
                )
            )
            document_tokens = _tokens(document)
            union = query_tokens | document_tokens
            score = (
                len(query_tokens & document_tokens)
                / len(union)
                if union
                else 0.0
            )
            if score > 0:
                matches.append((item, round(score, 6)))

        matches.sort(
            key=lambda pair: (
                pair[1],
                pair[0].published_at or 0,
            ),
            reverse=True,
        )
        return tuple(matches[:limit])

    @staticmethod
    def _serialize(item: IncidentPostmortem) -> str:
        payload = {
            **item.__dict__,
            "contributing_factors": list(
                item.contributing_factors
            ),
            "evidence": [
                evidence.__dict__
                for evidence in item.evidence
            ],
            "actions": [
                action.__dict__
                for action in item.actions
            ],
        }
        return json.dumps(
            payload,
            ensure_ascii=False,
            separators=(",", ":"),
        )

    @staticmethod
    def _deserialize(
        payload: str,
    ) -> IncidentPostmortem:
        raw = json.loads(payload)
        raw["contributing_factors"] = tuple(
            raw.get("contributing_factors", ())
        )
        raw["evidence"] = tuple(
            PostmortemEvidence(**item)
            for item in raw.get("evidence", ())
        )
        raw["actions"] = tuple(
            PostmortemAction(**item)
            for item in raw.get("actions", ())
        )
        return IncidentPostmortem(**raw)

    def _item_key(self, postmortem_id: str) -> str:
        return f"{self.prefix}:item:{postmortem_id}"

    def _incident_key(self, incident_id: str) -> str:
        return f"{self.prefix}:incident:{incident_id}"

    def _tenant_index(self, tenant_id: str) -> str:
        return f"{self.prefix}:tenant:{tenant_id}"


class PostmortemKnowledgeService:
    def __init__(
        self,
        *,
        repository,
        incident_repository,
    ):
        self.repository = repository
        self.incident_repository = incident_repository

    def create_from_incident(
        self,
        *,
        incident_id: str,
        title: str,
        summary: str,
        now: int | None = None,
    ) -> IncidentPostmortem:
        existing = self.repository.get_by_incident(
            incident_id
        )
        if existing is not None:
            return existing

        incident = self._incident(incident_id)
        current = int(
            now if now is not None
            else time.time()
        )
        postmortem_id = hashlib.sha256(
            f"{incident.tenant_id}|{incident_id}".encode(
                "utf-8"
            )
        ).hexdigest()

        item = IncidentPostmortem(
            postmortem_id=postmortem_id,
            incident_id=incident_id,
            tenant_id=incident.tenant_id,
            title=title.strip(),
            summary=summary.strip(),
            root_cause="",
            impact="",
            lessons="",
            contributing_factors=(),
            evidence=(),
            actions=(),
            status="DRAFT",
            revision=1,
            created_at=current,
            updated_at=current,
            published_at=None,
        )
        return self.repository.save(item)

    def update_analysis(
        self,
        *,
        postmortem_id: str,
        root_cause: str,
        impact: str,
        lessons: str,
        contributing_factors: tuple[str, ...],
        expected_revision: int,
        now: int | None = None,
    ) -> IncidentPostmortem:
        item = self._editable(postmortem_id)
        updated = IncidentPostmortem(
            **{
                **item.__dict__,
                "root_cause": root_cause.strip(),
                "impact": impact.strip(),
                "lessons": lessons.strip(),
                "contributing_factors": tuple(
                    factor.strip()
                    for factor in contributing_factors
                    if factor.strip()
                ),
                "revision": item.revision + 1,
                "updated_at": int(
                    now if now is not None
                    else time.time()
                ),
            }
        )
        return self.repository.save(
            updated,
            expected_revision=expected_revision,
        )

    def add_evidence(
        self,
        *,
        postmortem_id: str,
        kind: str,
        summary: str,
        reference: str | None,
        expected_revision: int,
        now: int | None = None,
    ) -> IncidentPostmortem:
        item = self._editable(postmortem_id)
        current = int(
            now if now is not None
            else time.time()
        )
        evidence_id = hashlib.sha256(
            (
                f"{postmortem_id}|{kind}|"
                f"{summary}|{current}"
            ).encode("utf-8")
        ).hexdigest()
        evidence = PostmortemEvidence(
            evidence_id=evidence_id,
            kind=kind.upper(),
            summary=summary.strip(),
            reference=reference,
            recorded_at=current,
        )
        updated = IncidentPostmortem(
            **{
                **item.__dict__,
                "evidence": item.evidence + (evidence,),
                "revision": item.revision + 1,
                "updated_at": current,
            }
        )
        return self.repository.save(
            updated,
            expected_revision=expected_revision,
        )

    def add_action(
        self,
        *,
        postmortem_id: str,
        title: str,
        owner: str,
        due_at: int | None,
        expected_revision: int,
        now: int | None = None,
    ) -> IncidentPostmortem:
        item = self._editable(postmortem_id)
        current = int(
            now if now is not None
            else time.time()
        )
        action_id = hashlib.sha256(
            (
                f"{postmortem_id}|{title}|"
                f"{owner}|{current}"
            ).encode("utf-8")
        ).hexdigest()
        action = PostmortemAction(
            action_id=action_id,
            title=title.strip(),
            owner=owner.strip(),
            due_at=due_at,
            status="OPEN",
            completed_at=None,
        )
        updated = IncidentPostmortem(
            **{
                **item.__dict__,
                "actions": item.actions + (action,),
                "revision": item.revision + 1,
                "updated_at": current,
            }
        )
        return self.repository.save(
            updated,
            expected_revision=expected_revision,
        )

    def complete_action(
        self,
        *,
        postmortem_id: str,
        action_id: str,
        expected_revision: int,
        now: int | None = None,
    ) -> IncidentPostmortem:
        item = self._editable(postmortem_id)
        current = int(
            now if now is not None
            else time.time()
        )
        found = False
        actions = []
        for action in item.actions:
            if action.action_id != action_id:
                actions.append(action)
                continue
            found = True
            actions.append(
                PostmortemAction(
                    **{
                        **action.__dict__,
                        "status": "COMPLETED",
                        "completed_at": current,
                    }
                )
            )
        if not found:
            raise KeyError(
                "Postmortem action bulunamadı"
            )

        updated = IncidentPostmortem(
            **{
                **item.__dict__,
                "actions": tuple(actions),
                "revision": item.revision + 1,
                "updated_at": current,
            }
        )
        return self.repository.save(
            updated,
            expected_revision=expected_revision,
        )

    def publish(
        self,
        *,
        postmortem_id: str,
        expected_revision: int,
        now: int | None = None,
    ) -> IncidentPostmortem:
        item = self._editable(postmortem_id)
        incident = self._incident(item.incident_id)

        if incident.status != "RESOLVED":
            raise PostmortemValidationError(
                "Incident çözülmeden postmortem yayınlanamaz"
            )
        if not item.root_cause:
            raise PostmortemValidationError(
                "Root cause zorunludur"
            )
        if not item.impact:
            raise PostmortemValidationError(
                "Impact zorunludur"
            )
        if not item.evidence:
            raise PostmortemValidationError(
                "En az bir evidence zorunludur"
            )
        if not item.actions:
            raise PostmortemValidationError(
                "En az bir action zorunludur"
            )

        current = int(
            now if now is not None
            else time.time()
        )
        published = IncidentPostmortem(
            **{
                **item.__dict__,
                "status": "PUBLISHED",
                "revision": item.revision + 1,
                "updated_at": current,
                "published_at": current,
            }
        )
        return self.repository.save(
            published,
            expected_revision=expected_revision,
        )

    def _editable(
        self,
        postmortem_id: str,
    ) -> IncidentPostmortem:
        item = self.repository.get(postmortem_id)
        if item is None:
            raise KeyError(
                "Postmortem bulunamadı"
            )
        if item.status == "PUBLISHED":
            raise PostmortemConflict(
                "Yayınlanmış postmortem değiştirilemez"
            )
        return item

    def _incident(self, incident_id: str):
        incident = self.incident_repository.get_incident(
            incident_id
        )
        if incident is None:
            raise KeyError(
                "Alert incident bulunamadı"
            )
        return incident


_TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9çğıöşüÇĞİÖŞÜ]+")


def _tokens(value: str) -> set[str]:
    return {
        token.casefold()
        for token in _TOKEN_PATTERN.findall(value)
        if len(token) > 2
    }
