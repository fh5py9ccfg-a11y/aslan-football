from __future__ import annotations

from dataclasses import dataclass
import json
import time


@dataclass(frozen=True)
class FeatureDefinition:
    name: str
    version: str
    entity_type: str
    value_type: str
    owner: str
    ttl_seconds: int
    max_age_seconds: int
    status: str
    source: str
    transformation: str
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class FeatureValue:
    tenant_id: str
    entity_id: str
    feature_name: str
    feature_version: str
    value: object
    event_time: int
    ingested_at: int
    expires_at: int | None
    source: str


@dataclass(frozen=True)
class FeatureFreshness:
    feature_name: str
    feature_version: str
    entity_id: str
    event_time: int
    age_seconds: int
    max_age_seconds: int
    fresh: bool


class FeatureValidationError(ValueError):
    pass


class RedisFeatureStore:
    def __init__(
        self,
        client,
        *,
        prefix: str = "aslan:feature-store",
        offline_limit: int = 1000,
    ):
        self.client = client
        self.prefix = prefix
        self.offline_limit = offline_limit

    def register_definition(
        self,
        definition: FeatureDefinition,
    ) -> FeatureDefinition:
        self.client.set(
            self._definition_key(
                definition.name,
                definition.version,
            ),
            json.dumps(
                definition.__dict__,
                ensure_ascii=False,
                separators=(",", ":"),
            ),
        )
        self.client.sadd(
            self._definition_index(),
            f"{definition.name}:{definition.version}",
        )
        return definition

    def get_definition(
        self,
        name: str,
        version: str,
    ) -> FeatureDefinition | None:
        payload = self.client.get(
            self._definition_key(name, version)
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return FeatureDefinition(**json.loads(payload))

    def list_definitions(
        self,
    ) -> tuple[FeatureDefinition, ...]:
        items = []
        for token in self.client.smembers(
            self._definition_index()
        ):
            if isinstance(token, bytes):
                token = token.decode("utf-8")
            name, version = str(token).rsplit(":", 1)
            item = self.get_definition(name, version)
            if item is not None:
                items.append(item)
        items.sort(
            key=lambda item: (
                item.name,
                item.version,
            )
        )
        return tuple(items)

    def put(
        self,
        value: FeatureValue,
    ) -> FeatureValue:
        definition = self.get_definition(
            value.feature_name,
            value.feature_version,
        )
        if definition is None:
            raise KeyError(
                "Feature definition bulunamadı"
            )

        self._validate_value(
            definition,
            value.value,
        )

        payload = json.dumps(
            value.__dict__,
            ensure_ascii=False,
            separators=(",", ":"),
        )
        ttl = max(
            1,
            definition.ttl_seconds,
        )
        self.client.setex(
            self._online_key(
                value.tenant_id,
                value.entity_id,
                value.feature_name,
                value.feature_version,
            ),
            ttl,
            payload,
        )
        self.client.zadd(
            self._offline_key(
                value.tenant_id,
                value.entity_id,
                value.feature_name,
                value.feature_version,
            ),
            {
                payload: float(value.event_time)
            },
        )
        self.client.zremrangebyrank(
            self._offline_key(
                value.tenant_id,
                value.entity_id,
                value.feature_name,
                value.feature_version,
            ),
            0,
            -(self.offline_limit + 1),
        )
        return value

    def get_online(
        self,
        *,
        tenant_id: str,
        entity_id: str,
        feature_name: str,
        feature_version: str,
    ) -> FeatureValue | None:
        payload = self.client.get(
            self._online_key(
                tenant_id,
                entity_id,
                feature_name,
                feature_version,
            )
        )
        if payload is None:
            return None
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return FeatureValue(**json.loads(payload))

    def get_as_of(
        self,
        *,
        tenant_id: str,
        entity_id: str,
        feature_name: str,
        feature_version: str,
        as_of: int,
    ) -> FeatureValue | None:
        results = self.client.zrevrangebyscore(
            self._offline_key(
                tenant_id,
                entity_id,
                feature_name,
                feature_version,
            ),
            as_of,
            "-inf",
            start=0,
            num=1,
        )
        if not results:
            return None
        payload = results[0]
        if isinstance(payload, bytes):
            payload = payload.decode("utf-8")
        return FeatureValue(**json.loads(payload))

    def freshness(
        self,
        *,
        tenant_id: str,
        entity_id: str,
        feature_name: str,
        feature_version: str,
        now: int | None = None,
    ) -> FeatureFreshness:
        definition = self.get_definition(
            feature_name,
            feature_version,
        )
        if definition is None:
            raise KeyError(
                "Feature definition bulunamadı"
            )
        value = self.get_online(
            tenant_id=tenant_id,
            entity_id=entity_id,
            feature_name=feature_name,
            feature_version=feature_version,
        )
        if value is None:
            raise KeyError(
                "Online feature değeri bulunamadı"
            )

        current = int(
            now if now is not None
            else time.time()
        )
        age = max(
            0,
            current - value.event_time,
        )
        return FeatureFreshness(
            feature_name=feature_name,
            feature_version=feature_version,
            entity_id=entity_id,
            event_time=value.event_time,
            age_seconds=age,
            max_age_seconds=(
                definition.max_age_seconds
            ),
            fresh=(
                age <= definition.max_age_seconds
            ),
        )

    @staticmethod
    def _validate_value(
        definition: FeatureDefinition,
        value,
    ) -> None:
        expected = definition.value_type.upper()

        if expected == "FLOAT":
            if not isinstance(
                value,
                (int, float),
            ) or isinstance(value, bool):
                raise FeatureValidationError(
                    "FLOAT feature sayısal olmalıdır"
                )
        elif expected == "INT":
            if not isinstance(value, int) or isinstance(
                value,
                bool,
            ):
                raise FeatureValidationError(
                    "INT feature tam sayı olmalıdır"
                )
        elif expected == "STRING":
            if not isinstance(value, str):
                raise FeatureValidationError(
                    "STRING feature metin olmalıdır"
                )
        elif expected == "BOOL":
            if not isinstance(value, bool):
                raise FeatureValidationError(
                    "BOOL feature boolean olmalıdır"
                )
        else:
            raise FeatureValidationError(
                f"Desteklenmeyen feature type: {expected}"
            )

    def _definition_key(
        self,
        name: str,
        version: str,
    ) -> str:
        return (
            f"{self.prefix}:definition:"
            f"{name}:{version}"
        )

    def _definition_index(self) -> str:
        return f"{self.prefix}:definitions"

    def _online_key(
        self,
        tenant_id: str,
        entity_id: str,
        feature_name: str,
        feature_version: str,
    ) -> str:
        return (
            f"{self.prefix}:online:{tenant_id}:"
            f"{entity_id}:{feature_name}:"
            f"{feature_version}"
        )

    def _offline_key(
        self,
        tenant_id: str,
        entity_id: str,
        feature_name: str,
        feature_version: str,
    ) -> str:
        return (
            f"{self.prefix}:offline:{tenant_id}:"
            f"{entity_id}:{feature_name}:"
            f"{feature_version}"
        )


class FeatureLineageService:
    def __init__(self, *, store):
        self.store = store

    def describe(
        self,
        *,
        feature_name: str,
        feature_version: str,
    ) -> dict:
        definition = self.store.get_definition(
            feature_name,
            feature_version,
        )
        if definition is None:
            raise KeyError(
                "Feature definition bulunamadı"
            )

        return {
            "feature": (
                f"{definition.name}:"
                f"{definition.version}"
            ),
            "entity_type": definition.entity_type,
            "source": definition.source,
            "transformation": (
                definition.transformation
            ),
            "owner": definition.owner,
            "status": definition.status,
        }
