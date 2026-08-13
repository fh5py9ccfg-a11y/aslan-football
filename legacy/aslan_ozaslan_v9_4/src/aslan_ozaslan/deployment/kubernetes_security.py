from __future__ import annotations

from dataclasses import dataclass
import base64
import json


@dataclass(frozen=True)
class KubernetesSecret:
    name: str
    namespace: str
    data: dict[str, str]


@dataclass(frozen=True)
class KubernetesConfig:
    name: str
    namespace: str
    data: dict[str, str]


class KubernetesSecurityRenderer:
    def render_secret(self, secret: KubernetesSecret) -> str:
        if not secret.name.strip() or not secret.namespace.strip():
            raise ValueError("Secret adı ve namespace boş olamaz")
        if not secret.data:
            raise ValueError("Secret verisi boş olamaz")

        encoded = {
            key: base64.b64encode(value.encode("utf-8")).decode("ascii")
            for key, value in secret.data.items()
        }
        return json.dumps(
            {
                "apiVersion": "v1",
                "kind": "Secret",
                "metadata": {
                    "name": secret.name,
                    "namespace": secret.namespace,
                },
                "type": "Opaque",
                "data": encoded,
            },
            ensure_ascii=False,
            sort_keys=True,
        )

    def render_config(self, config: KubernetesConfig) -> str:
        if not config.name.strip() or not config.namespace.strip():
            raise ValueError("Config adı ve namespace boş olamaz")
        return json.dumps(
            {
                "apiVersion": "v1",
                "kind": "ConfigMap",
                "metadata": {
                    "name": config.name,
                    "namespace": config.namespace,
                },
                "data": dict(config.data),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
